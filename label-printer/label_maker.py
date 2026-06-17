"""Génération de l'image d'une étiquette pour Brother QL-570.

Compose du texte, un QR code, un code-barres et/ou une image sur une
étiquette aux dimensions du rouleau DK choisi. L'image produite est en
niveaux de gris (mode "L") prête à être convertie par brother_ql.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field

from PIL import Image, ImageDraw, ImageFont
from brother_ql.labels import ALL_LABELS

# La QL-570 imprime à 300 dpi et accepte des rouleaux jusqu'à 62 mm.
DPI = 300
MODEL = "QL-570"


def _supported_labels():
    """Retourne les étiquettes compatibles QL-570 (largeur <= 62 mm)."""
    labels = []
    for lab in ALL_LABELS:
        # restricted_to_models vide => compatible toutes imprimantes QL
        if lab.restricted_to_models and not any(
            "QL-570" in m or "QL-5" in m for m in lab.restricted_to_models
        ):
            continue
        width_dots = lab.dots_printable[0]
        if width_dots == 0 or width_dots > 696:  # 62 mm = 696 pts à 300 dpi
            continue
        labels.append(lab)
    return labels


def list_labels():
    """Liste des formats pour l'UI (identifiant + libellé lisible)."""
    out = []
    for lab in _supported_labels():
        w, h = lab.dots_printable
        if h == 0:
            desc = f"{lab.identifier} — continu {lab.tape_size[0]}mm"
        else:
            desc = f"{lab.identifier} — {lab.tape_size[0]}x{lab.tape_size[1]}mm"
        out.append({"id": lab.identifier, "name": desc, "continuous": h == 0})
    # Tri : continu d'abord puis prédécoupé, par largeur
    out.sort(key=lambda x: (not x["continuous"], x["name"]))
    return out


def _label_spec(identifier: str):
    for lab in ALL_LABELS:
        if lab.identifier == identifier:
            return lab
    raise ValueError(f"Format d'étiquette inconnu : {identifier}")


def _load_font(size: int, bold: bool = False):
    candidates = (
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
        if bold
        else [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _make_qr(data: str, box: int = 10):
    import qrcode

    qr = qrcode.QRCode(border=1, box_size=box,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("L")


def _make_barcode(data: str, symbology: str = "code128"):
    import barcode
    from barcode.writer import ImageWriter

    cls = barcode.get_barcode_class(symbology)
    writer = ImageWriter()
    bc = cls(data, writer=writer)
    buf = io.BytesIO()
    bc.write(buf, options={"module_height": 12.0, "font_size": 8,
                           "text_distance": 3, "quiet_zone": 2})
    buf.seek(0)
    return Image.open(buf).convert("L")


@dataclass
class LabelContent:
    label: str = "62"            # identifiant du rouleau DK
    text: str = ""
    font_size: int = 0           # 0 => auto
    bold: bool = True
    align: str = "center"        # left / center / right
    qr_data: str = ""
    barcode_data: str = ""
    barcode_type: str = "code128"
    image_bytes: bytes | None = field(default=None, repr=False)
    length_mm: int = 0           # longueur pour rouleau continu (0 => auto)
    margin: int = 16             # marge en pixels


def render(content: LabelContent) -> Image.Image:
    """Construit l'image finale de l'étiquette."""
    spec = _label_spec(content.label)
    width = spec.dots_printable[0]
    fixed_height = spec.dots_printable[1]
    continuous = fixed_height == 0

    margin = content.margin
    inner_w = width - 2 * margin
    if inner_w < 10:
        inner_w = width

    # --- Construction des blocs (de haut en bas) ---
    blocks: list[Image.Image] = []

    if content.image_bytes:
        im = Image.open(io.BytesIO(content.image_bytes)).convert("L")
        if im.width > inner_w:
            ratio = inner_w / im.width
            im = im.resize((inner_w, int(im.height * ratio)))
        blocks.append(im)

    if content.qr_data.strip():
        qr = _make_qr(content.qr_data.strip())
        target = min(inner_w, 360)
        qr = qr.resize((target, target), Image.NEAREST)
        blocks.append(qr)

    if content.text.strip():
        blocks.append(_render_text_block(content, inner_w))

    if content.barcode_data.strip():
        bc = _make_barcode(content.barcode_data.strip(), content.barcode_type)
        if bc.width > inner_w:
            ratio = inner_w / bc.width
            bc = bc.resize((inner_w, int(bc.height * ratio)))
        blocks.append(bc)

    if not blocks:
        blocks.append(_render_text_block(
            LabelContent(text="(étiquette vide)", font_size=36), inner_w))

    spacing = 12
    content_h = sum(b.height for b in blocks) + spacing * (len(blocks) - 1)

    # --- Hauteur finale du canevas ---
    if continuous:
        if content.length_mm > 0:
            height = int(content.length_mm / 25.4 * DPI)
        else:
            height = content_h + 2 * margin
        height = max(height, content_h + 2 * margin)
    else:
        height = fixed_height

    canvas = Image.new("L", (width, height), 255)
    y = max(margin, (height - content_h) // 2)
    for b in blocks:
        x = (width - b.width) // 2
        canvas.paste(b, (x, y))
        y += b.height + spacing

    return canvas


def _render_text_block(content: LabelContent, inner_w: int) -> Image.Image:
    text = content.text.strip()
    lines = text.split("\n")

    if content.font_size > 0:
        size = content.font_size
    else:
        # Auto : on cherche la plus grande taille qui tient en largeur
        size = 20
        while size < 200:
            font = _load_font(size + 8, content.bold)
            longest = max(lines, key=len)
            w = font.getbbox(longest)[2]
            if w > inner_w:
                break
            size += 8

    font = _load_font(size, content.bold)
    line_heights, line_widths = [], []
    for ln in lines:
        bbox = font.getbbox(ln or " ")
        line_widths.append(bbox[2] - bbox[0])
        line_heights.append(bbox[3] - bbox[1])
    pad = max(8, size // 4)
    block_h = sum(line_heights) + pad * (len(lines) - 1) + 8
    block_w = max(max(line_widths), 1) + 8

    img = Image.new("L", (max(block_w, inner_w), block_h), 255)
    draw = ImageDraw.Draw(img)
    y = 4
    for ln, lw, lh in zip(lines, line_widths, line_heights):
        if content.align == "left":
            x = 0
        elif content.align == "right":
            x = img.width - lw
        else:
            x = (img.width - lw) // 2
        draw.text((x, y), ln, font=font, fill=0)
        y += lh + pad
    return img


def render_png(content: LabelContent) -> bytes:
    img = render(content)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
