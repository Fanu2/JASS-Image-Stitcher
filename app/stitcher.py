from __future__ import annotations

from pathlib import Path
import re
from PIL import Image, ImageOps, ImageDraw, ImageFont

SUPPORTED = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}


def natural_key(path: Path):
    return [int(x) if x.isdigit() else x.lower()
            for x in re.split(r"(\d+)", path.name)]


def image_files(folder: str | Path) -> list[Path]:
    folder = Path(folder)
    return sorted(
        [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED],
        key=natural_key,
    )


def load_images(paths):
    images = []
    for path in paths:
        with Image.open(path) as im:
            # Respect camera EXIF orientation, then keep native pixel dimensions.
            img = ImageOps.exif_transpose(im)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA")
            else:
                img = img.copy()
            images.append(img)
    return images


def _label_image(img: Image.Image, text: str, background) -> Image.Image:
    """Add a small label without resampling the source image."""
    label_h = 32
    out = Image.new("RGBA", (img.width, img.height + label_h), background)
    if img.mode == "RGBA":
        out.alpha_composite(img, (0, label_h))
    else:
        out.paste(img, (0, label_h))
    draw = ImageDraw.Draw(out)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
    draw.text((8, 7), text, fill=(0, 0, 0, 255), font=font)
    return out


def stitch_vertical(images, gap=0, background=(255, 255, 255, 255),
                    labels=False, label_names=None):
    if not images:
        raise ValueError("No images supplied")

    prepared = []
    for i, img in enumerate(images):
        item = img
        if labels:
            name = label_names[i] if label_names and i < len(label_names) else f"Image {i+1}"
            item = _label_image(item, name, background)
        prepared.append(item)

    width = max(im.width for im in prepared)
    height = sum(im.height for im in prepared) + gap * (len(prepared) - 1)
    canvas = Image.new("RGBA", (width, height), background)

    y = 0
    for im in prepared:
        x = (width - im.width) // 2
        canvas.alpha_composite(im.convert("RGBA"), (x, y))
        y += im.height + gap

    return canvas


def stitch_horizontal(images, gap=0, background=(255, 255, 255, 255),
                      labels=False, label_names=None):
    if not images:
        raise ValueError("No images supplied")

    prepared = []
    for i, img in enumerate(images):
        item = img
        if labels:
            name = label_names[i] if label_names and i < len(label_names) else f"Image {i+1}"
            item = _label_image(item, name, background)
        prepared.append(item)

    height = max(im.height for im in prepared)
    width = sum(im.width for im in prepared) + gap * (len(prepared) - 1)
    canvas = Image.new("RGBA", (width, height), background)

    x = 0
    for im in prepared:
        y = (height - im.height) // 2
        canvas.alpha_composite(im.convert("RGBA"), (x, y))
        x += im.width + gap

    return canvas


def stitch(paths, direction="vertical", gap=0, background=(255, 255, 255, 255),
           labels=False):
    paths = list(paths)
    images = load_images(paths)
    names = [Path(p).name for p in paths]
    if direction.lower().startswith("h"):
        return stitch_horizontal(images, gap, background, labels, names)
    return stitch_vertical(images, gap, background, labels, names)
