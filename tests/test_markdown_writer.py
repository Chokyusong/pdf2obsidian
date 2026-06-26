from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from pdf2obsidian.core.markdown_writer import (
    PDF_CONVERSION_PROFILE,
    write_image_markdown,
    write_pdf_markdown,
)


def test_write_pdf_markdown_uses_manage_pdf_profile(tmp_path):
    markdown_path = tmp_path / "sample.md"
    pdf_result = _pdf_result()

    write_pdf_markdown(
        markdown_path,
        title="sample",
        source_file="sample.pdf",
        pdf_result=pdf_result,
        include_page_separator=True,
        asset_link_prefix="Files/sample",
        created=date(2026, 6, 25),
    )

    content = markdown_path.read_text(encoding="utf-8")

    assert 'title: "sample"' in content
    assert 'source_file: "sample.pdf"' in content
    assert 'created: "2026-06-25"' in content
    assert '<p align="center"><sub>PDF 1페이지</sub></p>' in content
    assert "![[Files/sample/page_001.webp]]" not in content
    assert "## Main Title" in content
    assert "**Important** paragraph text." in content
    assert "Visual line one\n\nVisual line two" in content
    assert "| Step | Asset |" in content
    assert "![[Files/sample/p001-img01.webp]]" in content
    assert "Conversion profile: manage-pdf-in-obsidian" in content
    assert "Verification: full PDF pages are not inserted" in content


def test_write_pdf_markdown_keeps_table_region_fallback(tmp_path):
    markdown_path = tmp_path / "sample.md"
    pdf_result = _pdf_result(
        tables=[
            SimpleNamespace(
                page_number=1,
                markdown=None,
                row_count=2,
                col_count=2,
                bbox=(10.0, 10.0, 100.0, 100.0),
                asset_name="p001-table01.webp",
                warning="Table was too irregular for reliable Markdown.",
            )
        ],
        markdown_table_count=0,
        table_image_count=1,
        warning_count=1,
    )

    write_pdf_markdown(
        markdown_path,
        title="sample",
        source_file="sample.pdf",
        pdf_result=pdf_result,
        asset_link_prefix="Files/sample",
    )

    content = markdown_path.read_text(encoding="utf-8")

    assert "![[Files/sample/p001-table01.webp]]" in content
    assert "Table note: Table was too irregular" in content
    assert "Markdown tables: 0" in content
    assert "Table image fallbacks: 1" in content


def test_write_pdf_markdown_reports_links_and_size(tmp_path):
    markdown_path = tmp_path / "sample.md"
    pdf_result = _pdf_result()

    write_pdf_markdown(
        markdown_path,
        title="sample",
        source_file="sample.pdf",
        pdf_result=pdf_result,
        asset_link_prefix="Files/sample",
    )

    content = markdown_path.read_text(encoding="utf-8")

    assert "- [https://example.com](https://example.com)" in content
    assert "- Markdown size:" in content
    assert "- Extracted PDF links: 1" in content
    assert PDF_CONVERSION_PROFILE in content


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


def _pdf_result(
    text: str = (
        "## Main Title\n\n"
        "**Important** paragraph text.\n\n"
        "Visual line one\n\nVisual line two\n\n"
        "- Keep this list item"
    ),
    tables: list[SimpleNamespace] | None = None,
    markdown_table_count: int = 1,
    table_image_count: int = 0,
    warning_count: int = 0,
):
    if tables is None:
        tables = [
            SimpleNamespace(
                page_number=1,
                markdown="| Step | Asset |\n| --- | --- |\n| Week 1 | Card news |",
                row_count=2,
                col_count=2,
                bbox=(10.0, 10.0, 100.0, 100.0),
                asset_name=None,
                warning=None,
            )
        ]

    pages = [
        SimpleNamespace(
            page_number=1,
            page_asset_name=None,
            text=text,
            raw_text="Main Title\nImportant paragraph text.",
            tables=tables,
            images=[
                SimpleNamespace(
                    page_number=1,
                    asset_name="p001-img01.webp",
                    width=640,
                    height=480,
                    source_xref=10,
                )
            ],
            links=[
                SimpleNamespace(
                    label="https://example.com",
                    target="https://example.com",
                    kind="uri",
                )
            ],
            ocr_warning=None,
            warnings=[],
        ),
        SimpleNamespace(
            page_number=2,
            page_asset_name=None,
            text="Second page text.",
            raw_text="Second page text.",
            tables=[],
            images=[],
            links=[],
            ocr_warning=None,
            warnings=[],
        ),
    ]
    return SimpleNamespace(
        pages=pages,
        page_count=2,
        text_char_count=29,
        table_count=len(tables),
        markdown_table_count=markdown_table_count,
        table_image_count=table_image_count,
        image_count=1,
        link_count=1,
        ocr_page_count=0,
        warning_count=warning_count,
        source_size_bytes=10_000,
        asset_size_bytes=2_000,
        size_reduction_percent=80.0,
    )
