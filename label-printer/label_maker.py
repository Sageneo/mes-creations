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
    if bold:
        candidates = [
            # Linux
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            # Windows
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "arialbd.ttf",
            # macOS
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ]
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
    qr_size_mm: int = 0          # 0 => auto
    barcode_data: str = ""
    barcode_type: str = "code128"
    image_bytes: bytes | None = field(default=None, repr=False)
    length_mm: int = 0           # longueur pour rouleau continu (0 => auto)
    rotate: bool = False         # pivoter le contenu de 90°
    margin: int = 16             # marge en pixels


def render(content: LabelContent) -> Image.Image:
    """Construit l'image finale de l'étiquette.

    Si ``content.rotate`` est vrai, le contenu est composé « en paysage »
    (le texte court le long de la longueur de l'étiquette) puis l'image est
    pivotée de 90° pour respecter l'orientation d'impression.
    """
    spec = _label_spec(content.label)
    head = spec.dots_printable[0]        # largeur tête (axe transversal, fixe)
    length = spec.dots_printable[1]      # longueur (0 => rouleau continu)
    continuous = length == 0

    margin = content.margin

    if content.rotate:
        # Composition en paysage : l'axe horizontal devient la longueur.
        avail_w = length                 # 0 => continu (largeur libre)
        cross = head                     # hauteur de composition fixée à la tête
    else:
        avail_w = head                   # largeur de composition fixée à la tête
        cross = length                   # 0 => continu (hauteur libre)

    if avail_w > 0:
        inner_w = max(10, avail_w - 2 * margin)
    else:
        # Largeur libre (continu pivoté) : on borne large, la taille du texte
        # est limitée par la hauteur (cross) via max_h.
        inner_w = 4000
    max_h = (cross - 2 * margin) if cross > 0 else None

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
        if content.qr_size_mm > 0:
            target = int(content.qr_size_mm / 25.4 * DPI)
        else:
            target = min(inner_w, 360)
        if max_h:
            target = min(target, max_h)
        target = max(40, min(target, inner_w))
        qr = qr.resize((target, target), Image.NEAREST)
        blocks.append(qr)

    if content.text.strip():
        blocks.append(_render_text_block(content, inner_w, max_h))

    if content.barcode_data.strip():
        bc = _make_barcode(content.barcode_data.strip(), content.barcode_type)
        if bc.width > inner_w:
            ratio = inner_w / bc.width
            bc = bc.resize((inner_w, int(bc.height * ratio)))
        blocks.append(bc)

    if not blocks:
        blocks.append(_render_text_block(
            LabelContent(text="(étiquette vide)", font_size=36), inner_w, max_h))

    spacing = 12
    content_w = max(b.width for b in blocks)
    content_h = sum(b.height for b in blocks) + spacing * (len(blocks) - 1)

    # --- Dimensions du canevas de composition ---
    if avail_w > 0:
        canvas_w = avail_w
    else:
        canvas_w = content_w + 2 * margin

    if cross > 0:
        canvas_h = cross
    elif content.length_mm > 0:   # continu non pivoté avec longueur imposée
        canvas_h = max(int(content.length_mm / 25.4 * DPI),
                       content_h + 2 * margin)
    else:
        canvas_h = content_h + 2 * margin

    canvas = Image.new("L", (canvas_w, canvas_h), 255)
    y = max(margin, (canvas_h - content_h) // 2)
    for b in blocks:
        x = (canvas_w - b.width) // 2
        canvas.paste(b, (x, y))
        y += b.height + spacing

    if content.rotate:
        canvas = canvas.transpose(Image.ROTATE_90)

    return canvas


def _render_text_block(content: LabelContent, inner_w: int,
                       max_h: int | None = None) -> Image.Image:
    text = content.text.strip() or " "
    spacing = 8
    probe = ImageDraw.Draw(Image.new("L", (1, 1)))

    def bbox_for(size: int):
        font = _load_font(size, content.bold)
        bbox = probe.multiline_textbbox(
            (0, 0), text, font=font, spacing=spacing, align=content.align)
        return font, bbox

    if content.font_size > 0:
        size = content.font_size
    else:
        # Auto : plus grande taille qui tient en largeur (et en hauteur si
        # une contrainte max_h est fournie — utile pour les étiquettes
        # prédécoupées ou le contenu pivoté).
        size = 12
        while size < 400:
            _, bbox = bbox_for(size + 4)
            too_wide = (bbox[2] - bbox[0]) > inner_w
            too_tall = max_h is not None and (bbox[3] - bbox[1]) > max_h
            if too_wide or too_tall:
                break
            size += 4

    font, bbox = bbox_for(size)
    text_w = int(bbox[2] - bbox[0])
    text_h = int(bbox[3] - bbox[1])
    pad = max(6, size // 6)

    img_w = int(max(text_w + 2 * pad, inner_w))
    img_h = int(text_h + 2 * pad)
    img = Image.new("L", (img_w, img_h), 255)
    draw = ImageDraw.Draw(img)

    # On retranche l'offset du bbox pour ne jamais rogner glyphes/accents.
    if content.align == "left":
        x = pad - bbox[0]
    elif content.align == "right":
        x = img_w - text_w - pad - bbox[0]
    else:
        x = (img_w - text_w) // 2 - bbox[0]
    y = pad - bbox[1]
    draw.multiline_text((x, y), text, font=font, fill=0,
                        spacing=spacing, align=content.align)
    return img


def render_png(content: LabelContent) -> bytes:
    img = render(content)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
