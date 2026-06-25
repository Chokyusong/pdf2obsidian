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
    assert result.pages[0].tables[0].row_count == 3
    assert "| Step | Asset | Difficulty |" in result.pages[0].tables[0].markdown
    assert "| Week 1 | Card news | 1 star |" in result.pages[0].tables[0].markdown
    assert "Step\nAsset\nDifficulty" not in result.pages[0].text
    assert (assets_dir / "page_001.webp").exists()
