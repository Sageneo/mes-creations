"""Registre des codes matériel imprimés (suivi anti-doublon).

Format de code : PREFIXE-AA-NNNN  (ex. ECR-26-1000)
  - PREFIXE : liste fermée (voir PREFIXES)
  - AA      : 2 chiffres de l'année
  - NNNN    : numéro séquentiel 4 chiffres (1000 -> 9999), par (préfixe, année)

Les codes imprimés sont mémorisés dans registry.json afin d'éviter les
doublons. Une réimpression explicite reste possible (étiquette perdue/abîmée).
"""

from __future__ import annotations

import datetime
import json
import os
import re

REGISTRY_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "registry.json")

# Zone 1 — préfixes autorisés (liste fermée)
PREFIXES = {
    "PC": "Ordinateur (générique)",
    "PCF": "Ordinateur fixe",
    "PCP": "Ordinateur portable",
    "ECR": "Écran",
    "DCK": "Station d'accueil (docking)",
    "TAB": "Tablette",
}

NUM_MIN = 1000
NUM_MAX = 9999

CODE_RE = re.compile(r"^(PC|PCF|PCP|ECR|DCK|TAB)-\d{2}-\d{4}$")


def current_yy() -> str:
    return datetime.date.today().strftime("%y")


def year_options(span_before: int = 2, span_after: int = 6):
    """Liste d'années (AA) autour de l'année courante pour le menu déroulant."""
    y = datetime.date.today().year
    return [f"{(y + i) % 100:02d}" for i in range(-span_before, span_after + 1)]


def format_code(prefix: str, year: str | int, number: int) -> str:
    yy = int(year) % 100
    return f"{prefix}-{yy:02d}-{int(number):04d}"


def validate(prefix: str, year, number) -> str | None:
    """Retourne un message d'erreur, ou None si valide."""
    if prefix not in PREFIXES:
        return f"Préfixe « {prefix} » non autorisé."
    try:
        yy = int(year)
    except (TypeError, ValueError):
        return "Année invalide."
    if not (0 <= yy <= 99):
        return "L'année doit tenir sur 2 chiffres (00-99)."
    try:
        n = int(number)
    except (TypeError, ValueError):
        return "Numéro invalide."
    if not (NUM_MIN <= n <= NUM_MAX):
        return f"Le numéro doit être compris entre {NUM_MIN} et {NUM_MAX}."
    return None


def _load() -> dict:
    try:
        with open(REGISTRY_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        data = {}
    data.setdefault("codes", {})
    return data


def _save(data: dict) -> None:
    with open(REGISTRY_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def is_used(code: str) -> bool:
    return code in _load()["codes"]


def info(code: str) -> dict | None:
    return _load()["codes"].get(code)


def record(code: str) -> dict:
    """Enregistre (ou ré-enregistre) une impression du code."""
    data = _load()
    now = datetime.datetime.now().isoformat(timespec="seconds")
    entry = data["codes"].get(code)
    if entry:
        entry["count"] = entry.get("count", 1) + 1
        entry["last_printed"] = now
    else:
        entry = {"count": 1, "first_printed": now, "last_printed": now}
        data["codes"][code] = entry
    _save(data)
    return entry


def next_number(prefix: str, year) -> int:
    """Prochain numéro libre pour le couple (préfixe, année)."""
    yy = int(year) % 100
    head = f"{prefix}-{yy:02d}-"
    used = [
        int(code.rsplit("-", 1)[1])
        for code in _load()["codes"]
        if code.startswith(head)
    ]
    return max(used) + 1 if used else NUM_MIN


def build_series(prefix: str, year, start: int, end: int | None = None):
    """Liste de codes de start à end (inclus). end=None => un seul code."""
    end = start if end is None else end
    return [format_code(prefix, year, n) for n in range(int(start), int(end) + 1)]


def list_codes() -> list[dict]:
    data = _load()
    out = [{"code": c, **v} for c, v in data["codes"].items()]
    out.sort(key=lambda x: x["code"])
    return out
