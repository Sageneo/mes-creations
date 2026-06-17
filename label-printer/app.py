"""Interface web Flask pour imprimer des étiquettes sur Brother QL-570."""

from __future__ import annotations

import base64
import io
import os

from flask import Flask, jsonify, render_template, request, send_file

import label_maker
import printer

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 Mo max


def _content_from_request(form, files) -> label_maker.LabelContent:
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

    return label_maker.LabelContent(
        label=form.get("label", "62"),
        text=form.get("text", ""),
        font_size=as_int("font_size", 0),
        bold=form.get("bold", "true") in ("true", "on", "1"),
        align=form.get("align", "center"),
        qr_data=form.get("qr_data", ""),
        barcode_data=form.get("barcode_data", ""),
        barcode_type=form.get("barcode_type", "code128"),
        image_bytes=image_bytes,
        length_mm=as_int("length_mm", 0),
    )


@app.route("/")
def index():
    return render_template(
        "index.html",
        labels=label_maker.list_labels(),
        printer=printer.default_printer(),
    )


@app.route("/api/labels")
def api_labels():
    return jsonify(label_maker.list_labels())


@app.route("/api/printers")
def api_printers():
    return jsonify({
        "default": printer.default_printer(),
        "detected": printer.discover(),
    })


@app.route("/api/preview", methods=["POST"])
def api_preview():
    try:
        content = _content_from_request(request.form, request.files)
        png = label_maker.render_png(content)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 400
    return send_file(io.BytesIO(png), mimetype="image/png")


@app.route("/api/print", methods=["POST"])
def api_print():
    try:
        content = _content_from_request(request.form, request.files)
        image = label_maker.render(content)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"success": False, "message": f"Erreur de rendu : {exc}"}), 400

    chosen_printer = request.form.get("printer") or printer.default_printer()
    cut = request.form.get("cut", "true") in ("true", "on", "1")
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


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5000"))
    app.run(host=host, port=port, debug=os.environ.get("DEBUG") == "1")
