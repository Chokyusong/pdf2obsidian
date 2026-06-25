from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

PDF_IMPORT_TEXT = "text_markdown"
PDF_IMPORT_PAGE_IMAGE = "page_image_markdown"
PDF_IMPORT_TEXT_PAGE_IMAGE = "text_page_image_markdown"
PDF_IMPORT_MODES = {
    PDF_IMPORT_TEXT,
    PDF_IMPORT_PAGE_IMAGE,
    PDF_IMPORT_TEXT_PAGE_IMAGE,
}


def _yaml_value(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _frontmatter(title: str, source_file: str, doc_type: str, created: date | None = None) -> str:
    created_date = created or date.today()
    return "\n".join(
        [
            "---",
            f"title: {_yaml_value(title)}",
            f"source_file: {_yaml_value(source_file)}",
            f'created: "{created_date.isoformat()}"',
            f"type: {_yaml_value(doc_type)}",
            "---",
            "",
        ]
    )


def _preserve_markdown_linebreaks(text: str) -> str:
    """Use Markdown hard breaks so Obsidian preview keeps PDF line boundaries."""
    paragraphs = text.split("\n\n")
    rendered: list[str] = []

    for paragraph in paragraphs:
        lines = [line.rstrip() for line in paragraph.splitlines()]
        hard_lines = [f"{line}  " if line else "" for line in lines]
        rendered.append("\n".join(hard_lines).rstrip())

    return "\n\n".join(part for part in rendered if part)


def write_pdf_markdown(
    markdown_path: str | Path,
    title: str,
    source_file: str,
    pdf_result: Any,
    include_page_separator: bool = True,
    pdf_import_mode: str = PDF_IMPORT_TEXT_PAGE_IMAGE,
    created: date | None = None,
) -> Path:
    path = Path(markdown_path)
    selected_mode = (
        pdf_import_mode if pdf_import_mode in PDF_IMPORT_MODES else PDF_IMPORT_TEXT_PAGE_IMAGE
    )
    lines = [_frontmatter(title, source_file, "pdf-import", created), f"# {title}", ""]

    for index, page in enumerate(pdf_result.pages):
        if include_page_separator and index > 0:
            lines.extend(["---", ""])
        lines.extend(
            [
                f"## Page {page.page_number}",
                "",
            ]
        )

        if selected_mode in {PDF_IMPORT_PAGE_IMAGE, PDF_IMPORT_TEXT_PAGE_IMAGE}:
            lines.extend([f"![[assets/{page.page_asset_name}]]", ""])

        if selected_mode in {PDF_IMPORT_TEXT, PDF_IMPORT_TEXT_PAGE_IMAGE}:
            for table_index, table in enumerate(page.tables, start=1):
                lines.extend(
                    [
                        f"### Extracted table {table_index}",
                        "",
                        table.markdown,
                        "",
                    ]
                )

            if selected_mode == PDF_IMPORT_TEXT_PAGE_IMAGE:
                lines.extend(["### Extracted text", ""])

            if page.text:
                lines.extend([_preserve_markdown_linebreaks(page.text), ""])
            else:
                lines.extend(["> No extractable text was found on this page.", ""])

        if selected_mode in {PDF_IMPORT_TEXT, PDF_IMPORT_TEXT_PAGE_IMAGE}:
            for image in page.images:
                lines.extend(
                    [
                        f"### Extracted image {image.asset_name}",
                        "",
                        f"![[assets/{image.asset_name}]]",
                        "",
                    ]
                )

        if page.ocr_warning:
            lines.extend([f"> OCR note: {page.ocr_warning}", ""])

    lines.extend(["---", "", "## Conversion Report", ""])
    lines.extend(
        [
            f"- Source pages: {pdf_result.page_count}",
            f"- Extracted text characters: {pdf_result.text_char_count}",
            f"- Extracted PDF tables: {pdf_result.table_count}",
            f"- Extracted PDF images: {pdf_result.image_count}",
            f"- Original PDF size: {pdf_result.source_size_bytes:,} bytes",
            f"- Saved asset size: {pdf_result.asset_size_bytes:,} bytes",
            f"- PDF import mode: {selected_mode}",
        ]
    )
    if pdf_result.size_reduction_percent is not None:
        reduction = pdf_result.size_reduction_percent
        lines.append(f"- Asset size reduction vs original: {reduction:.1f}%")
    lines.extend(
        [
            "- Verification: text layer extraction was attempted before OCR.",
            "- Verification: each PDF page is rendered to WebP for visual layout fidelity.",
            "- Verification: PDF-embedded images are also extracted when large enough.",
        ]
    )

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def write_image_markdown(
    markdown_path: str | Path,
    title: str,
    source_file: str,
    image_result: Any,
    created: date | None = None,
) -> Path:
    path = Path(markdown_path)
    lines = [
        _frontmatter(title, source_file, "image-import", created),
        f"# {title}",
        "",
        f"![[assets/{image_result.asset_name}]]",
        "",
    ]

    if image_result.text:
        lines.extend([image_result.text, ""])
    if image_result.ocr_warning:
        lines.extend([f"> OCR note: {image_result.ocr_warning}", ""])

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path
