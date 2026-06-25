from __future__ import annotations

from io import BytesIO

import fitz
from PIL import Image

from pdf2obsidian.core.pdf_processor import process_pdf


def _sample_png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (240, 180), color=(40, 120, 200)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_process_pdf_extracts_text_page_render_and_embedded_images(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    assets_dir = tmp_path / "assets"

    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 72), "Hello PDF text layer")
    page.insert_image(fitz.Rect(72, 120, 312, 300), stream=_sample_png_bytes())
    document.save(pdf_path)
    document.close()

    result = process_pdf(pdf_path, assets_dir, quality=75, ocr_enabled=False)

    assert result.page_count == 1
    assert result.image_count == 1
    assert "Hello PDF text layer" in result.pages[0].text
    assert result.pages[0].page_asset_name == "page_001.webp"
    assert result.pages[0].images[0].asset_name.startswith("image_p001_")
    assert (assets_dir / "page_001.webp").exists()
    assert (assets_dir / result.pages[0].images[0].asset_name).exists()
