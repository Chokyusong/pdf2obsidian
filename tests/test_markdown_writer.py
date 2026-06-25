from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from pdf2obsidian.core.markdown_writer import write_image_markdown, write_pdf_markdown


def test_write_pdf_markdown_creates_obsidian_links(tmp_path):
    markdown_path = tmp_path / "sample.md"
    pages = [
        SimpleNamespace(
            page_number=1,
            text="First page text.",
            images=[
                SimpleNamespace(
                    page_number=1,
                    asset_name="image_p001_001.webp",
                    width=640,
                    height=480,
                    source_xref=10,
                )
            ],
            ocr_warning=None,
        ),
        SimpleNamespace(
            page_number=2,
            text="Second page text.",
            images=[],
            ocr_warning=None,
        ),
    ]
    pdf_result = SimpleNamespace(
        pages=pages,
        page_count=2,
        text_char_count=29,
        image_count=1,
        source_size_bytes=10_000,
        asset_size_bytes=2_000,
        size_reduction_percent=80.0,
    )

    write_pdf_markdown(
        markdown_path,
        title="sample",
        source_file="sample.pdf",
        pdf_result=pdf_result,
        include_page_separator=True,
        created=date(2026, 6, 25),
    )

    content = markdown_path.read_text(encoding="utf-8")

    assert 'title: "sample"' in content
    assert 'source_file: "sample.pdf"' in content
    assert 'created: "2026-06-25"' in content
    assert "![[assets/image_p001_001.webp]]" in content
    assert "![[assets/page_001.webp]]" not in content
    assert "## Page 1" in content
    assert "First page text." in content
    assert "## Conversion Report" in content
    assert "Extracted PDF images: 1" in content


def test_write_image_markdown_creates_image_import(tmp_path):
    markdown_path = tmp_path / "image.md"
    image = SimpleNamespace(asset_name="image_001.webp", text="OCR text.", ocr_warning=None)

    write_image_markdown(
        markdown_path,
        title="image",
        source_file="image.png",
        image_result=image,
        created=date(2026, 6, 25),
    )

    content = markdown_path.read_text(encoding="utf-8")

    assert 'type: "image-import"' in content
    assert "![[assets/image_001.webp]]" in content
    assert "OCR text." in content
