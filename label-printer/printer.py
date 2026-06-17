"""Envoi de l'étiquette à la Brother QL-570 via brother_ql."""

from __future__ import annotations

import os

from PIL import Image
from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send
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
