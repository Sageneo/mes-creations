"""Interface web Flask pour imprimer des étiquettes sur Brother QL-570."""

from __future__ import annotations

import base64
import io
import json
import os
import signal
import threading
import time

from flask import Flask, jsonify, render_template, request, send_file

import label_maker
import printer
import registry

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 Mo max

# Fichier de configuration persistante (à côté de ce script).
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# Champs sauvegardés comme valeurs par défaut au prochain démarrage.
CONFIG_KEYS = (
    "label", "length_mm", "font_size", "bold", "align",
    "qr_size_mm", "barcode_type", "printer", "cut", "rotate",
    "code_enabled", "code_prefix", "code_year", "code_qr", "code_barcode",
    "code_font_size",
)
DEFAULT_CONFIG = {
    "label": "62", "length_mm": "0", "font_size": "0", "bold": True,
    "align": "center", "qr_size_mm": "0", "barcode_type": "code128",
    "printer": printer.default_printer(), "cut": True, "rotate": False,
    "code_enabled": False, "code_prefix": "ECR",
    "code_year": registry.current_yy(), "code_qr": True, "code_barcode": False,
    "code_font_size": "0",
}
CONFIG_BOOL_KEYS = ("bold", "cut", "rotate", "code_enabled", "code_qr",
                    "code_barcode")


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, encoding="utf-8") as fh:
            cfg.update(json.load(fh))
    except (OSError, ValueError):
        pass
    return cfg


def save_config(form) -> dict:
    cfg = load_config()
    for key in CONFIG_KEYS:
        if key in CONFIG_BOOL_KEYS:
            cfg[key] = form.get(key, "") in ("true", "on", "1")
        elif key in form:
            cfg[key] = form.get(key)
    with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)
    return cfg


def _is_true(form, key):
    return form.get(key, "") in ("true", "on", "1")


def _content_from_request(form, files, code=None) -> label_maker.LabelContent:
    image_bytes = None
    if "image" in files and files["image"].filename:
        image_bytes = files["image"].read()
    elif form.get("image_b64"):
        try:
            image_bytes = base64.b64decode(form["image_b64"].split(",")[-1])
        except Exception:
            image_bytes = None

    def as_int(key, default=0):
        try:
            return int(form.get(key, default) or default)
        except ValueError:
            return default

    code_font_size = as_int("code_font_size", 0)
    barcode_caption = ""
    barcode_caption_size = 0
    if code is not None:
        # Mode « code matériel » : le contenu vient du code généré.
        use_qr = _is_true(form, "code_qr")
        use_barcode = _is_true(form, "code_barcode")
        qr_data = code if use_qr else ""
        barcode_data = code if use_barcode else ""
        barcode_type = "code128"   # supporte lettres + tirets
        barcode_text = False
        # Style classique : le code lisible est placé SOUS les barres, avec une
        # taille réglable. En QR seul, le code est affiché comme bloc texte.
        if use_barcode:
            barcode_caption = code
            barcode_caption_size = code_font_size
            text = ""
        else:
            text = code
    else:
        text = form.get("text", "")
        qr_data = form.get("qr_data", "")
        barcode_data = form.get("barcode_data", "")
        barcode_type = form.get("barcode_type", "code128")
        barcode_text = True

    # En mode code, la taille du texte (QR seul) vient du champ dédié.
    font_size = code_font_size if code is not None else as_int("font_size", 0)

    return label_maker.LabelContent(
        label=form.get("label", "62"),
        text=text,
        font_size=font_size,
        bold=_is_true(form, "bold"),
        align=form.get("align", "center"),
        qr_data=qr_data,
        qr_size_mm=as_int("qr_size_mm", 0),
        barcode_data=barcode_data,
        barcode_type=barcode_type,
        barcode_text=barcode_text,
        barcode_caption=barcode_caption,
        barcode_caption_size=barcode_caption_size,
        image_bytes=image_bytes,
        length_mm=as_int("length_mm", 0),
        rotate=_is_true(form, "rotate"),
    )


def _code_series_from_form(form):
    """Construit la liste de codes demandée. Retourne (codes, erreur)."""
    prefix = form.get("code_prefix", "")
    year = form.get("code_year", registry.current_yy())
    try:
        start = int(form.get("code_number", "") or 0)
    except ValueError:
        return [], "Numéro de départ invalide."
    series = _is_true(form, "code_series")
    if series:
        try:
            end = int(form.get("code_number_end", "") or 0)
        except ValueError:
            return [], "Numéro de fin invalide."
    else:
        end = start
    if end < start:
        return [], "Le numéro de fin doit être ≥ au numéro de départ."

    err = registry.validate(prefix, year, start) or \
        registry.validate(prefix, year, end)
    if err:
        return [], err
    return registry.build_series(prefix, year, start, end), None


@app.route("/")
def index():
    return render_template(
        "index.html",
        labels=label_maker.list_labels(),
        cfg=load_config(),
        prefixes=registry.PREFIXES,
        years=registry.year_options(),
        current_yy=registry.current_yy(),
    )


@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        cfg = save_config(request.form)
        return jsonify({"saved": True, "config": cfg})
    return jsonify(load_config())


@app.route("/api/labels")
def api_labels():
    return jsonify(label_maker.list_labels())


@app.route("/api/media")
def api_media():
    chosen = request.args.get("printer") or printer.default_printer()
    return jsonify(printer.read_media_status(chosen))


@app.route("/api/printers")
def api_printers():
    return jsonify({
        "default": printer.default_printer(),
        "detected": printer.discover(),
    })


@app.route("/api/next-number")
def api_next_number():
    prefix = request.args.get("prefix", "")
    year = request.args.get("year", registry.current_yy())
    if prefix not in registry.PREFIXES:
        return jsonify({"error": "Préfixe non autorisé."}), 400
    return jsonify({"number": registry.next_number(prefix, year)})


@app.route("/api/check-code")
def api_check_code():
    """Indique si un code est déjà utilisé (et combien de fois)."""
    prefix = request.args.get("prefix", "")
    year = request.args.get("year", registry.current_yy())
    number = request.args.get("number", "")
    err = registry.validate(prefix, year, number)
    if err:
        return jsonify({"valid": False, "error": err}), 200
    code = registry.format_code(prefix, year, number)
    return jsonify({"valid": True, "code": code,
                    "used": registry.is_used(code),
                    "info": registry.info(code)})


@app.route("/api/registry")
def api_registry():
    return jsonify({"codes": registry.list_codes(),
                    "counters": registry.counters()})


@app.route("/registry")
def registry_page():
    return render_template("registry.html")


@app.route("/api/registry/export")
def api_registry_export():
    data = json.dumps(registry.export_data(), ensure_ascii=False, indent=2)
    buf = io.BytesIO(data.encode("utf-8"))
    fname = f"suivi-etiquettes-{registry.current_yy()}.json"
    return send_file(buf, mimetype="application/json",
                     as_attachment=True, download_name=fname)


@app.route("/api/registry/import", methods=["POST"])
def api_registry_import():
    merge = request.form.get("mode", "merge") != "replace"
    try:
        if "file" in request.files and request.files["file"].filename:
            payload = json.load(request.files["file"])
        else:
            payload = json.loads(request.form.get("data", ""))
        result = registry.import_data(payload, merge=merge)
    except (ValueError, json.JSONDecodeError) as exc:
        return jsonify({"success": False, "message": f"Import impossible : {exc}"}), 400
    return jsonify({"success": True, "message":
                    f"Import terminé : {result['added']} ajouté(s), "
                    f"{result['updated']} mis à jour, {result['total']} au total.",
                    **result})


@app.route("/api/registry/delete", methods=["POST"])
def api_registry_delete():
    code = request.form.get("code", "")
    ok = registry.delete(code)
    return jsonify({"success": ok,
                    "message": "Code supprimé." if ok else "Code introuvable."})


@app.route("/api/quit", methods=["POST"])
def api_quit():
    """Arrête proprement le serveur (utile quand il tourne sans terminal)."""
    def _shutdown():
        time.sleep(0.4)
        os.kill(os.getpid(), signal.SIGTERM)
    threading.Thread(target=_shutdown, daemon=True).start()
    return jsonify({"success": True, "message": "Serveur arrêté."})


@app.route("/api/preview", methods=["POST"])
def api_preview():
    try:
        code = None
        if _is_true(request.form, "code_enabled"):
            codes, err = _code_series_from_form(request.form)
            if err:
                return jsonify({"error": err}), 400
            code = codes[0]   # aperçu du premier code de la série
        content = _content_from_request(request.form, request.files, code=code)
        png = label_maker.render_png(content)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 400
    return send_file(io.BytesIO(png), mimetype="image/png")


@app.route("/api/print", methods=["POST"])
def api_print():
    # Mémorise les réglages utilisés pour les recharger au prochain lancement.
    try:
        save_config(request.form)
    except OSError:
        pass

    chosen_printer = request.form.get("printer") or printer.default_printer()
    cut = _is_true(request.form, "cut")

    if _is_true(request.form, "code_enabled"):
        return _print_codes(chosen_printer, cut)

    try:
        content = _content_from_request(request.form, request.files)
        image = label_maker.render(content)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"success": False, "message": f"Erreur de rendu : {exc}"}), 400
    try:
        result = printer.print_label(
            image, label=content.label, printer=chosen_printer, cut=cut
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({
            "success": False,
            "message": f"Échec de l'impression : {exc}",
            "hint": "Vérifiez que la QL-570 est branchée/allumée et que vous "
                    "avez les droits USB (voir README).",
        }), 500
    return jsonify(result)


def _print_codes(chosen_printer, cut):
    """Imprime une série de codes matériel, chacun découpé séparément."""
    codes, err = _code_series_from_form(request.form)
    if err:
        return jsonify({"success": False, "message": err}), 400

    reprint = _is_true(request.form, "code_reprint")
    # Vérifie les doublons avant impression (sauf réimpression explicite).
    if not reprint:
        already = [c for c in codes if registry.is_used(c)]
        if already:
            preview = ", ".join(already[:5]) + ("…" if len(already) > 5 else "")
            return jsonify({
                "success": False,
                "duplicate": True,
                "codes": already,
                "message": f"{len(already)} code(s) déjà imprimé(s) : {preview}. "
                           "Cochez « Réimpression » pour les réimprimer.",
            }), 409

    printed, errors = [], []
    for code in codes:
        try:
            content = _content_from_request(request.form, request.files, code=code)
            image = label_maker.render(content)
            printer.print_label(image, label=content.label,
                                printer=chosen_printer, cut=cut)
            registry.record(code)
            printed.append(code)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{code} : {exc}")
            break  # on arrête à la première erreur d'impression

    ok = bool(printed) and not errors
    msg = f"{len(printed)} étiquette(s) imprimée(s)."
    if printed:
        msg += f" ({printed[0]}" + (f" → {printed[-1]}" if len(printed) > 1 else "") + ")"
    if errors:
        msg += " ⚠️ Arrêt : " + errors[0]
    return jsonify({"success": ok, "message": msg,
                    "printed": printed, "errors": errors})


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    app.run(host=host, port=port, debug=os.environ.get("DEBUG") == "1")
