from __future__ import annotations

from io import BytesIO

import fitz
from PIL import Image

from pdf2obsidian.core.converter import ConversionOptions, convert_file


def _sample_png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (240, 180), color=(40, 120, 200)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_pdf_conversion_uses_files_folder_and_manage_pdf_profile(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    output_root = tmp_path / "output"

    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 72), "Main Heading", fontsize=22)
    page.insert_image(fitz.Rect(72, 120, 312, 300), stream=_sample_png_bytes())
    document.save(pdf_path)
    document.close()

    result = convert_file(pdf_path, ConversionOptions(output_root=output_root))

    markdown = result.markdown_path.read_text(encoding="utf-8")
    expected_asset = result.output_dir / "Files" / "sample" / "p001-img01.webp"

    assert expected_asset.exists()
    assert "![[Files/sample/p001-img01.webp]]" in markdown
    assert "Conversion profile: manage-pdf-in-obsidian" in markdown
    assert "page_001.webp" not in markdown
