from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
from xml.sax.saxutils import escape
from PIL import Image, ImageOps


def _mm(px: int, dpi: float = 96.0) -> float:
    return max(1.0, px * 25.4 / dpi)


def export_images_to_odg(paths, output_path: str | Path, dpi: float = 96.0):
    """Create a LibreOffice Draw .odg with one native image on each page.

    Source image files are embedded without recompression. Each Draw page is
    sized to the image's native pixel dimensions at the selected logical DPI.
    The raster pixels themselves are unchanged.
    """
    paths = [Path(p) for p in paths]
    if not paths:
        raise ValueError("No images supplied")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pictures = []
    pages = []
    styles = []

    for idx, src in enumerate(paths, 1):
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im)
            width, height = im.size
        w = _mm(width, dpi)
        h = _mm(height, dpi)
        style_name = f"dp{idx}"
        master_name = f"Master{idx}"
        href = f"Pictures/image{idx}{src.suffix.lower()}"
        pictures.append((href, src))
        styles.append((style_name, master_name, w, h))
        pages.append((idx, style_name, href, w, h, src.name))

    page_layouts = []
    master_pages = []
    for style_name, master_name, w, h in styles:
        page_layouts.append(
            f'<style:page-layout style:name="{style_name}">'
            f'<style:page-layout-properties fo:page-width="{w:.4f}mm" fo:page-height="{h:.4f}mm" '
            f'style:print-orientation="portrait"/></style:page-layout>'
        )
        master_pages.append(
            f'<style:master-page style:name="{master_name}" style:page-layout-name="{style_name}"/>'
        )

    style_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
 xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
 xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
 xmlns:xlink="http://www.w3.org/1999/xlink"
 xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
 office:version="1.3">
 <office:styles/>
 <office:automatic-styles>{''.join(page_layouts)}</office:automatic-styles>
 <office:master-styles>{''.join(master_pages)}</office:master-styles>
</office:document-styles>'''

    auto_styles = []
    for idx, (_, _, w, h) in enumerate(styles, 1):
        auto_styles.append(
            f'<style:style style:name="fr{idx}" style:family="graphic">'
            f'<style:graphic-properties draw:stroke="none" draw:fill="none"/></style:style>'
        )

    page_xml = []
    for idx, style_name, href, w, h, name in pages:
        page_xml.append(
            f'<draw:page draw:name="Page {idx}" draw:style-name="{style_name}" draw:master-page-name="Master{idx}">'
            f'<draw:frame draw:style-name="fr{idx}" svg:x="0mm" svg:y="0mm" '
            f'svg:width="{w:.4f}mm" svg:height="{h:.4f}mm" draw:z-index="0">'
            f'<draw:image xlink:href="{escape(href)}" xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad">'
            f'<text:p>{escape(name)}</text:p></draw:image></draw:frame></draw:page>'
        )

    content_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
 xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
 xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
 xmlns:xlink="http://www.w3.org/1999/xlink"
 xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
 office:version="1.3">
 <office:scripts/>
 <office:automatic-styles>{''.join(auto_styles)}</office:automatic-styles>
 <office:body><office:drawing>{''.join(page_xml)}</office:drawing></office:body>
</office:document-content>'''

    manifest_entries = [
        '<manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.graphics"/>',
        '<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>',
        '<manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>',
        '<manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>',
        '<manifest:file-entry manifest:full-path="settings.xml" manifest:media-type="text/xml"/>',
    ]
    for href, src in pictures:
        mime = Image.MIME.get(src.suffix.lower().lstrip('.'), 'image/png')
        manifest_entries.append(
            f'<manifest:file-entry manifest:full-path="{escape(href)}" manifest:media-type="{mime}"/>'
        )
    manifest_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.3">
{''.join(manifest_entries)}
</manifest:manifest>'''

    meta_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" office:version="1.3"><office:meta/></office:document-meta>'''
    settings_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<office:document-settings xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" office:version="1.3"><office:settings/></office:document-settings>'''

    with ZipFile(output_path, "w") as z:
        z.writestr("mimetype", "application/vnd.oasis.opendocument.graphics", compress_type=ZIP_STORED)
        z.writestr("content.xml", content_xml, compress_type=ZIP_DEFLATED)
        z.writestr("styles.xml", style_xml, compress_type=ZIP_DEFLATED)
        z.writestr("meta.xml", meta_xml, compress_type=ZIP_DEFLATED)
        z.writestr("settings.xml", settings_xml, compress_type=ZIP_DEFLATED)
        for href, src in pictures:
            z.write(src, href, compress_type=ZIP_STORED)

    return output_path
