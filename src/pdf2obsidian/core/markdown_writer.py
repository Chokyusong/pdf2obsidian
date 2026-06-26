from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

PDF_CONVERSION_PROFILE = "manage-pdf-in-obsidian"


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


def _page_label(page_number: int) -> str:
    return f'<p align="center"><sub>PDF {page_number}페이지</sub></p>'


def _wiki_image(asset_link_prefix: str, asset_name: str) -> str:
    return f"![[{asset_link_prefix}/{asset_name}]]"


def _write_tables(lines: list[str], page: Any, asset_link_prefix: str) -> None:
    for table_index, table in enumerate(page.tables, start=1):
        lines.extend([f"##### Table {table_index}", ""])
        if getattr(table, "markdown", None):
            lines.extend([table.markdown, ""])
        if getattr(table, "asset_name", None):
            lines.extend([_wiki_image(asset_link_prefix, table.asset_name), ""])
        if getattr(table, "warning", None):
            lines.extend([f"> Table note: {table.warning}", ""])


def _write_images(lines: list[str], page: Any, asset_link_prefix: str) -> None:
    for image_index, image in enumerate(page.images, start=1):
        lines.extend(
            [
                f"##### Image {image_index}",
                "",
                _wiki_image(asset_link_prefix, image.asset_name),
                "",
            ]
        )


def _write_links(lines: list[str], page: Any) -> None:
    links = getattr(page, "links", [])
    if not links:
        return

    lines.extend(["##### Links", ""])
    for link in links:
        if getattr(link, "kind", "") == "uri":
            lines.append(f"- [{link.label}]({link.target})")
        else:
            lines.append(f"- {link.label}: {link.target}")
    lines.append("")


def write_pdf_markdown(
    markdown_path: str | Path,
    title: str,
    source_file: str,
    pdf_result: Any,
    include_page_separator: bool = True,
    asset_link_prefix: str = "assets",
    created: date | None = None,
) -> Path:
    path = Path(markdown_path)
    lines = [_frontmatter(title, source_file, "pdf-import", created), f"# {title}", ""]

    for index, page in enumerate(pdf_result.pages):
        if include_page_separator and index > 0:
            lines.extend(["---", ""])

        lines.extend([_page_label(page.page_number), ""])
        if page.text:
            lines.extend([page.text, ""])
        else:
            lines.extend(["> No extractable text was found on this page.", ""])
        _write_tables(lines, page, asset_link_prefix)
        _write_images(lines, page, asset_link_prefix)
        _write_links(lines, page)

        if page.ocr_warning:
            lines.extend([f"> OCR note: {page.ocr_warning}", ""])
        for warning in getattr(page, "warnings", []) or []:
            lines.extend([f"> Conversion note: {warning}", ""])

    lines.extend(["---", "", "## Conversion Report", ""])
    lines.extend(
        [
            f"- Source pages: {pdf_result.page_count}",
            f"- Extracted text characters: {pdf_result.text_char_count}",
            f"- Detected PDF tables: {pdf_result.table_count}",
            f"- Markdown tables: {getattr(pdf_result, 'markdown_table_count', 0)}",
            f"- Table image fallbacks: {getattr(pdf_result, 'table_image_count', 0)}",
            f"- Extracted PDF images: {pdf_result.image_count}",
            f"- Extracted PDF links: {getattr(pdf_result, 'link_count', 0)}",
            f"- OCR pages: {getattr(pdf_result, 'ocr_page_count', 0)}",
            f"- Warnings: {getattr(pdf_result, 'warning_count', 0)}",
            f"- Original PDF size: {pdf_result.source_size_bytes:,} bytes",
            "- Markdown size: pending",
            f"- Saved asset size: {pdf_result.asset_size_bytes:,} bytes",
            f"- Conversion profile: {PDF_CONVERSION_PROFILE}",
        ]
    )
    if pdf_result.size_reduction_percent is not None:
        reduction = pdf_result.size_reduction_percent
        lines.append(f"- Asset size reduction vs original: {reduction:.1f}%")
    lines.extend(
        [
            "- Verification: text layer extraction was attempted before OCR.",
            "- Verification: full PDF pages are not inserted as default images.",
            "- Verification: only necessary PDF images and table-region fallbacks are saved.",
        ]
    )

    content = "\n".join(lines).rstrip() + "\n"
    markdown_size = len(content.encode("utf-8"))
    content = content.replace(
        "- Markdown size: pending",
        f"- Markdown size: {markdown_size:,} bytes",
    )
    path.write_text(content, encoding="utf-8")
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
