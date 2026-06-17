"""Envoi de l'étiquette à la Brother QL-570 via brother_ql."""

from __future__ import annotations

import os

from PIL import Image
from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send, interpret_response
from brother_ql.backends import backend_factory, guess_backend

MODEL = "QL-570"
# Identifiants USB de la QL-570
USB_VENDOR = 0x04F9
USB_PRODUCT = 0x2028


def default_printer() -> str:
    """Identifiant de l'imprimante : variable d'env ou valeur USB par défaut."""
    return os.environ.get(
        "QL_PRINTER", f"usb://0x{USB_VENDOR:04x}:0x{USB_PRODUCT:04x}"
    )


def sanitize_identifier(ident: str) -> str:
    """Nettoie un identifiant brother_ql potentiellement corrompu.

    Certaines QL-570 renvoient un numéro de série invalide (caractères non
    ASCII) que brother_ql colle à l'identifiant USB sous la forme
    ``usb://0x04f9:0x2028_<série>``. Ce suffixe casse l'analyse hexadécimale.
    On ne conserve donc que ``usb://0xVVVV:0xPPPP``.
    """
    if not ident:
        return ident
    if ident.startswith("usb://"):
        body = ident[len("usb://"):]
        # garde uniquement vendor:product, retire série (_… ou /…)
        for sep in ("_", "/"):
            body = body.split(sep, 1)[0]
        return "usb://" + body
    return ident


def discover():
    """Retourne la liste des imprimantes détectées (USB)."""
    found = []
    for backend in ("pyusb", "linux_kernel"):
        try:
            be = backend_factory(backend)
            for dev in be["list_available_devices"]():
                ident = dev.get("identifier") if isinstance(dev, dict) else dev
                found.append({
                    "backend": backend,
                    "identifier": sanitize_identifier(ident),
                })
        except Exception:
            continue
    return found


# Séquence de requête de statut Brother QL :
#   200 octets nuls (invalidation) + ESC @ (init) + ESC i S (demande statut)
_STATUS_REQUEST = b"\x00" * 200 + b"\x1b\x40" + b"\x1b\x69\x53"


def read_media_status(printer: str | None = None) -> dict:
    """Interroge l'imprimante et renvoie le média actuellement chargé.

    Retourne un dict avec au moins {"available": bool}. Si la lecture
    réussit : media_width (mm), media_length (mm, 0 = continu), media_type…
    """
    printer = sanitize_identifier(printer or default_printer())
    try:
        backend = guess_backend(printer)
    except Exception:
        backend = "pyusb"

    be = backend_factory(backend)
    dev = None
    try:
        dev = be["backend_class"](printer)
        dev.write(_STATUS_REQUEST)
        data = dev.read(32)
        if not data or len(data) < 32:
            return {"available": False,
                    "message": "Aucune réponse de l'imprimante."}
        info = interpret_response(data)
        info["available"] = True
        info["label"] = match_label(info.get("media_width", 0),
                                    info.get("media_length", 0))
        return info
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "message": str(exc)}
    finally:
        if dev is not None:
            try:
                dev.dispose()
            except Exception:
                pass


def match_label(width_mm: int, length_mm: int):
    """Trouve l'identifiant brother_ql correspondant au média détecté."""
    if not width_mm:
        return None
    from brother_ql.labels import ALL_LABELS

    continuous = not length_mm
    best = None
    for lab in ALL_LABELS:
        tw, tl = lab.tape_size
        if tw != width_mm:
            continue
        if continuous and tl == 0:
            return lab.identifier
        if not continuous and abs(tl - length_mm) <= 1:
            return lab.identifier
        best = best or lab.identifier
    return best


def print_label(image: Image.Image, label: str, printer: str | None = None,
                cut: bool = True, rotate: str = "auto",
                threshold: int = 70) -> dict:
    """Convertit et envoie l'image à l'imprimante.

    Retourne un dict {"success": bool, "message": str, ...}.
    """
    printer = sanitize_identifier(printer or default_printer())
    try:
        backend = guess_backend(printer)
    except Exception:
        backend = "pyusb"

    qlr = BrotherQLRaster(MODEL)
    qlr.exception_on_warning = True

    instructions = convert(
        qlr=qlr,
        images=[image],
        label=label,
        rotate=rotate,
        threshold=threshold,
        dither=False,
        compress=False,
        red=False,
        dpi_600=False,
        hq=True,
        cut=cut,
    )

    result = send(
        instructions=instructions,
        printer_identifier=printer,
        backend_identifier=backend,
        blocking=True,
    )
    ok = bool(result.get("did_print")) and bool(result.get("ready_for_next_job", True))
    return {
        "success": ok,
        "message": "Impression envoyée." if ok
        else "L'imprimante n'a pas confirmé l'impression.",
        "details": result,
    }
