# JASS Image Stitcher v1.2.0

A lightweight PySide6 application for stitching all supported images in a selected folder into one combined image, with optional PDF export.

## v1.2.0 — Original Quality / Lossless Stitching

- Preserves each source image's native pixel dimensions.
- **No automatic resizing or downscaling.**
- Vertical or horizontal stitching.
- Adjustable pixel gap.
- Optional filename labels.
- PNG output is lossless.
- JPEG output supports quality 1–100 and 4:4:4-style no-subsampling (`subsampling=0`).
- WEBP can be saved losslessly.
- PDF export preserves the complete stitched pixel dimensions.
- PDF DPI can be selected from 72–1200.
- Preview is scaled only for display; the saved result is not reduced.

## Important

For maximum quality, save the combined image as **PNG** or **lossless WEBP**. JPEG is inherently lossy even at quality 100.

## Install

```powershell
python -m pip install -r requirements.txt
python main.py
```

## Supported input

JPG, JPEG, PNG, BMP, GIF, TIFF/TIF and WEBP.

Original files are never modified.

## LibreOffice Draw export

Use **Save in LibreOffice Draw** to create an `.odg` document with **one image per Draw page**. The original image files are embedded without recompression, so this avoids the raster-quality loss seen with the previous Pillow PDF export.

Open the resulting `.odg` directly in LibreOffice Draw. Each page is sized to the image's native pixel dimensions at 96 DPI; the embedded raster pixels are unchanged.
