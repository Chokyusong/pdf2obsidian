from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from pdf2obsidian.core.markdown_writer import (
    PDF_IMPORT_PAGE_IMAGE,
    PDF_IMPORT_RAW_TEXT,
    PDF_IMPORT_STRUCTURED,
    write_image_markdown,
    write_pdf_markdown,
)


def test_structured_pdf_markdown_does_not_insert_page_image_by_default(tmp_path):
    markdown_path = tmp_path / "sample.md"
    pdf_result = _pdf_result()

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
    assert "![[assets/page_001.webp]]" not in content
    assert '<p align="center"><sub>PDF 1페이지</sub></p>' in content
    assert "## Main Title" in content
    assert "**Important** paragraph text." in content
    assert "| Step | Asset |" in content
    assert "![[assets/image_p001_001.webp]]" in content
    assert "PDF import mode: structured_markdown" in content
    assert "Verification: page images are only inserted" in content


def test_page_image_markdown_inserts_only_page_images(tmp_path):
    markdown_path = tmp_path / "sample.md"
    pdf_result = _pdf_result()

    write_pdf_markdown(
        markdown_path,
        title="sample",
        source_file="sample.pdf",
        pdf_result=pdf_result,
        pdf_import_mode=PDF_IMPORT_PAGE_IMAGE,
    )

    content = markdown_path.read_text(encoding="utf-8")

    assert "![[assets/page_001.webp]]" in content
    assert "## Main Title" not in content
    assert "| Step | Asset |" not in content
    assert "![[assets/image_p001_001.webp]]" not in content
    assert "PDF import mode: page_image_markdown" in content


def test_raw_text_markdown_outputs_raw_text_and_assets(tmp_path):
    markdown_path = tmp_path / "sample.md"
    pdf_result = _pdf_result(raw_text="Raw first line\nRaw second line")

    write_pdf_markdown(
        markdown_path,
        title="sample",
        source_file="sample.pdf",
        pdf_result=pdf_result,
        pdf_import_mode=PDF_IMPORT_RAW_TEXT,
    )

    content = markdown_path.read_text(encoding="utf-8")

    assert "![[assets/page_001.webp]]" not in content
    assert "Raw first line  \nRaw second line" in content
    assert "## Main Title" not in content
    assert "| Step | Asset |" in content
    assert "![[assets/image_p001_001.webp]]" in content
    assert "PDF import mode: raw_text_markdown" in content


def test_structured_markdown_keeps_table_image_fallback(tmp_path):
    markdown_path = tmp_path / "sample.md"
    pdf_result = _pdf_result(
        tables=[
            SimpleNamespace(
                page_number=1,
                markdown=None,
                row_count=2,
                col_count=2,
                bbox=(10.0, 10.0, 100.0, 100.0),
                asset_name="table_p001_001.webp",
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
        pdf_import_mode=PDF_IMPORT_STRUCTURED,
    )

    content = markdown_path.read_text(encoding="utf-8")

    assert "![[assets/table_p001_001.webp]]" in content
    assert "Table note: Table was too irregular" in content
    assert "Markdown tables: 0" in content
    assert "Table image fallbacks: 1" in content


def test_legacy_text_page_image_mode_maps_to_structured_without_page_image(tmp_path):
    markdown_path = tmp_path / "sample.md"
    pdf_result = _pdf_result()

    write_pdf_markdown(
        markdown_path,
        title="sample",
        source_file="sample.pdf",
        pdf_result=pdf_result,
        pdf_import_mode="text_page_image_markdown",
    )

    content = markdown_path.read_text(encoding="utf-8")

    assert "![[assets/page_001.webp]]" not in content
    assert "PDF import mode: structured_markdown" in content


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
    text: str = "## Main Title\n\n**Important** paragraph text.\n\n- Keep this list item",
    raw_text: str = "Main Title\nImportant paragraph text.\n- Keep this list item",
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
            page_asset_name="page_001.webp",
            text=text,
            raw_text=raw_text,
            tables=tables,
            images=[
                SimpleNamespace(
                    page_number=1,
                    asset_name="image_p001_001.webp",
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
            page_asset_name="page_002.webp",
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
