from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any


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


def write_pdf_markdown(
    markdown_path: str | Path,
    title: str,
    source_file: str,
    pdf_result: Any,
    include_page_separator: bool = True,
    created: date | None = None,
) -> Path:
    path = Path(markdown_path)
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

        if page.text:
            lines.extend([page.text, ""])
        else:
            lines.extend(["> No extractable text was found on this page.", ""])

        for image in page.images:
            lines.extend(
                [
                    f'<p align="center"><sub>PDF {page.page_number}페이지 이미지</sub></p>',
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
            f"- Extracted PDF images: {pdf_result.image_count}",
            f"- Original PDF size: {pdf_result.source_size_bytes:,} bytes",
            f"- Saved asset size: {pdf_result.asset_size_bytes:,} bytes",
        ]
    )
    if pdf_result.size_reduction_percent is not None:
        reduction = pdf_result.size_reduction_percent
        lines.append(f"- Asset size reduction vs original: {reduction:.1f}%")
    lines.extend(
        [
            "- Verification: text layer extraction was attempted before OCR.",
            "- Verification: page images are not rendered by default.",
            "- Verification: only PDF-embedded images are saved.",
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
