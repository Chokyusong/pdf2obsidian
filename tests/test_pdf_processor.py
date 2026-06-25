from __future__ import annotations

from io import BytesIO

import fitz
from PIL import Image

from pdf2obsidian.core import ocr
from pdf2obsidian.core.pdf_processor import process_pdf


def _sample_png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (240, 180), color=(40, 120, 200)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_process_pdf_extracts_structured_text_and_embedded_images_without_page_render(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    assets_dir = tmp_path / "assets"

    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 72), "Main Heading", fontsize=22)
    page.insert_text((72, 110), "Important", fontsize=12, fontname="Helvetica-Bold")
    page.insert_text((72, 138), "- First list item", fontsize=12)
    page.insert_image(fitz.Rect(72, 180, 312, 360), stream=_sample_png_bytes())
    document.save(pdf_path)
    document.close()

    result = process_pdf(pdf_path, assets_dir, quality=75, ocr_enabled=False)

    assert result.page_count == 1
    assert result.image_count == 1
    assert "## Main Heading" in result.pages[0].text
    assert "**Important**" in result.pages[0].text
    assert "- First list item" in result.pages[0].text
    assert result.pages[0].page_asset_name is None
    assert result.pages[0].images[0].asset_name.startswith("image_p001_")
    assert not (assets_dir / "page_001.webp").exists()
    assert (assets_dir / result.pages[0].images[0].asset_name).exists()


def test_process_pdf_renders_page_only_when_requested(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    assets_dir = tmp_path / "assets"

    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 72), "Hello PDF text layer")
    document.save(pdf_path)
    document.close()

    result = process_pdf(pdf_path, assets_dir, quality=75, render_pages=True)

    assert result.pages[0].page_asset_name == "page_001.webp"
    assert (assets_dir / "page_001.webp").exists()


def test_process_pdf_uses_ocr_render_only_when_text_is_missing(tmp_path, monkeypatch):
    pdf_path = tmp_path / "scan.pdf"
    assets_dir = tmp_path / "assets"

    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_image(fitz.Rect(72, 72, 312, 252), stream=_sample_png_bytes())
    document.save(pdf_path)
    document.close()

    monkeypatch.setattr(
        ocr,
        "extract_text",
        lambda image_path: ocr.OCRResult(text="OCR fallback text", engine="test"),
    )

    result = process_pdf(pdf_path, assets_dir, quality=75, ocr_enabled=True)

    assert result.ocr_page_count == 1
    assert result.pages[0].ocr_used is True
    assert result.pages[0].page_asset_name is None
    assert result.pages[0].text == "OCR fallback text"
    assert (assets_dir / "ocr_page_001.webp").exists()
    assert not (assets_dir / "page_001.webp").exists()


def test_process_pdf_extracts_detected_table_as_markdown(tmp_path):
    pdf_path = tmp_path / "table.pdf"
    assets_dir = tmp_path / "assets"

    document = fitz.open()
    page = document.new_page(width=400, height=300)
    rect = fitz.Rect(50, 50, 350, 150)
    rows = 3
    cols = 3
    cell_width = rect.width / cols
    cell_height = rect.height / rows

    for row in range(rows + 1):
        y = rect.y0 + row * cell_height
        page.draw_line((rect.x0, y), (rect.x1, y))
    for col in range(cols + 1):
        x = rect.x0 + col * cell_width
        page.draw_line((x, rect.y0), (x, rect.y1))

    data = [
        ["Step", "Asset", "Difficulty"],
        ["Week 1", "Card news", "1 star"],
        ["Week 2", "Series", "2 stars"],
    ]
    for row, values in enumerate(data):
        for col, value in enumerate(values):
            page.insert_text(
                (rect.x0 + col * cell_width + 8, rect.y0 + row * cell_height + 22),
                value,
                fontsize=10,
            )

    document.save(pdf_path)
    document.close()

    result = process_pdf(pdf_path, assets_dir, quality=75, ocr_enabled=False)

    assert result.table_count == 1
    assert result.markdown_table_count == 1
    assert result.pages[0].tables[0].row_count == 3
    assert "| Step | Asset | Difficulty |" in result.pages[0].tables[0].markdown
    assert "| Week 1 | Card news | 1 star |" in result.pages[0].tables[0].markdown
    assert "Step\nAsset\nDifficulty" not in result.pages[0].text
    assert not (assets_dir / "page_001.webp").exists()
