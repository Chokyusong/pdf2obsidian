from __future__ import annotations

from io import BytesIO

import fitz
from PIL import Image, ImageDraw

from pdf2obsidian.core import ocr
from pdf2obsidian.core.pdf_processor import process_pdf


def _sample_png_bytes() -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (240, 180), color=(40, 120, 200))
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 220, 80), fill=(20, 20, 40))
    draw.rectangle((40, 105, 180, 150), fill=(240, 120, 40))
    draw.text((52, 118), "PDF IMAGE", fill=(255, 255, 255))
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _white_png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (240, 180), color=(255, 255, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_process_pdf_extracts_structured_text_and_embedded_images_without_page_render(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    assets_dir = tmp_path / "assets"

    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 72), "Main Heading", fontsize=22)
    page.insert_text((72, 110), "Important", fontsize=12, fontname="Helvetica-Bold")
    page.insert_text((72, 138), "First paragraph line", fontsize=12)
    page.insert_text((72, 166), "Second paragraph line", fontsize=12)
    page.insert_text((72, 194), "- First list item", fontsize=12)
    page.insert_image(fitz.Rect(72, 236, 312, 416), stream=_sample_png_bytes())
    document.save(pdf_path)
    document.close()

    result = process_pdf(pdf_path, assets_dir, quality=75, ocr_enabled=False)

    assert result.page_count == 1
    assert result.image_count == 1
    assert "## Main Heading" in result.pages[0].text
    assert "**Important**" in result.pages[0].text
    assert "First paragraph line\n\nSecond paragraph line" in result.pages[0].text
    assert "- First list item" in result.pages[0].text
    assert result.pages[0].page_asset_name is None
    assert result.pages[0].images[0].asset_name == "p001-img01.webp"
    assert not (assets_dir / "page_001.webp").exists()
    assert (assets_dir / result.pages[0].images[0].asset_name).exists()


def test_process_pdf_skips_blank_images_and_keeps_real_images_sequential(tmp_path):
    pdf_path = tmp_path / "images.pdf"
    assets_dir = tmp_path / "assets"

    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_image(fitz.Rect(72, 72, 312, 252), stream=_white_png_bytes())
    page.insert_image(fitz.Rect(72, 300, 312, 480), stream=_sample_png_bytes())
    document.save(pdf_path)
    document.close()

    result = process_pdf(pdf_path, assets_dir, quality=75, ocr_enabled=False)

    assert result.image_count == 1
    assert result.pages[0].images[0].asset_name == "p001-img01.webp"
    assert (assets_dir / "p001-img01.webp").exists()
    assert not (assets_dir / "p001-img02.webp").exists()


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
    assert not (assets_dir / "ocr_page_001.webp").exists()
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
