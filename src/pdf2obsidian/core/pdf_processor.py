from __future__ import annotations

import contextlib
import re
from dataclasses import dataclass
from io import BytesIO, StringIO
from pathlib import Path

import fitz
from PIL import Image

from pdf2obsidian.core import ocr


@dataclass(frozen=True)
class PDFImageResult:
    page_number: int
    asset_name: str
    width: int
    height: int
    source_xref: int


@dataclass(frozen=True)
class PDFTableResult:
    page_number: int
    markdown: str | None
    row_count: int
    col_count: int
    bbox: tuple[float, float, float, float]
    asset_name: str | None = None
    warning: str | None = None


@dataclass(frozen=True)
class PDFLinkResult:
    page_number: int
    label: str
    target: str
    kind: str


@dataclass(frozen=True)
class PDFPageResult:
    page_number: int
    text: str
    raw_text: str
    tables: list[PDFTableResult]
    images: list[PDFImageResult]
    links: list[PDFLinkResult]
    page_asset_name: str | None = None
    ocr_used: bool = False
    ocr_warning: str | None = None
    warnings: list[str] | None = None


@dataclass(frozen=True)
class PDFDocumentResult:
    source_size_bytes: int
    asset_size_bytes: int
    pages: list[PDFPageResult]

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def image_count(self) -> int:
        return sum(len(page.images) for page in self.pages)

    @property
    def table_count(self) -> int:
        return sum(len(page.tables) for page in self.pages)

    @property
    def markdown_table_count(self) -> int:
        return sum(1 for page in self.pages for table in page.tables if table.markdown)

    @property
    def table_image_count(self) -> int:
        return sum(1 for page in self.pages for table in page.tables if table.asset_name)

    @property
    def link_count(self) -> int:
        return sum(len(page.links) for page in self.pages)

    @property
    def ocr_page_count(self) -> int:
        return sum(1 for page in self.pages if page.ocr_used)

    @property
    def warning_count(self) -> int:
        count = 0
        for page in self.pages:
            count += len(page.warnings or [])
            count += sum(1 for table in page.tables if table.warning)
            if page.ocr_warning:
                count += 1
        return count

    @property
    def text_char_count(self) -> int:
        return sum(len(page.text) for page in self.pages)

    @property
    def size_reduction_percent(self) -> float | None:
        if self.source_size_bytes <= 0:
            return None
        return max(0.0, (1 - (self.asset_size_bytes / self.source_size_bytes)) * 100)


def _clean_pdf_text(text: str) -> str:
    for char in ["\u200b", "\u200c", "\u200d", "\ufeff", "\u00a0"]:
        text = text.replace(char, " ")
    lines = [line.rstrip() for line in text.splitlines()]
    paragraphs: list[str] = []
    buffer: list[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            if buffer:
                paragraphs.append("\n".join(buffer).strip())
                buffer = []
            continue

        buffer.append(line)

    if buffer:
        paragraphs.append("\n".join(buffer).strip())

    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)


def _intersects_table(
    block_bbox: tuple[float, float, float, float],
    table_bboxes: list[fitz.Rect],
) -> bool:
    block_rect = fitz.Rect(block_bbox)
    block_area = max(block_rect.get_area(), 1)

    for table_rect in table_bboxes:
        overlap = block_rect & table_rect
        if not overlap.is_empty and overlap.get_area() / block_area > 0.4:
            return True

    return False


@dataclass(frozen=True)
class _TextLine:
    text: str
    plain_text: str
    size: float
    bold_ratio: float
    bbox: tuple[float, float, float, float]


def _span_is_bold(span: dict) -> bool:
    font_name = str(span.get("font", "")).lower()
    flags = int(span.get("flags", 0))
    return bool(flags & 16) or "bold" in font_name or "black" in font_name


def _markdown_bold(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    if text.startswith("**") and text.endswith("**"):
        return text
    return f"**{text}**"


def _format_span_text(text: str, bold: bool) -> str:
    if not text.strip():
        return text
    return _markdown_bold(text) if bold else text


def _collect_text_lines(page: fitz.Page, table_bboxes: list[fitz.Rect]) -> list[_TextLine]:
    lines: list[_TextLine] = []
    text_dict = page.get_text("dict", sort=True)

    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        if _intersects_table(block.get("bbox", (0, 0, 0, 0)), table_bboxes):
            continue

        for line in block.get("lines", []):
            rendered_parts: list[str] = []
            plain_parts: list[str] = []
            sizes: list[float] = []
            bold_chars = 0
            total_chars = 0

            for span in line.get("spans", []):
                span_text = str(span.get("text", ""))
                if not span_text:
                    continue

                bold = _span_is_bold(span)
                rendered_parts.append(_format_span_text(span_text, bold))
                plain_parts.append(span_text)
                sizes.append(float(span.get("size", 0.0)))
                plain_length = len(span_text.strip())
                total_chars += plain_length
                if bold:
                    bold_chars += plain_length

            plain_text = "".join(plain_parts).strip()
            rendered_text = "".join(rendered_parts).strip()
            if not plain_text:
                continue

            lines.append(
                _TextLine(
                    text=rendered_text,
                    plain_text=plain_text,
                    size=max(sizes) if sizes else 0.0,
                    bold_ratio=(bold_chars / total_chars) if total_chars else 0.0,
                    bbox=tuple(float(value) for value in line.get("bbox", (0, 0, 0, 0))),
                )
            )

    return lines


def _body_font_size(lines: list[_TextLine]) -> float:
    sizes = sorted(line.size for line in lines if line.size > 0)
    if not sizes:
        return 0.0
    return sizes[len(sizes) // 2]


def _is_list_line(text: str) -> bool:
    return bool(
        re.match(r"^(\s*)([-*]\s+|[•◦▪]\s+|\d+[.)]\s+|\[[ xX]\]\s+)", text)
    )


def _is_heading_candidate(line: _TextLine, body_size: float) -> int:
    text = line.plain_text.strip()
    if not text:
        return 0
    if len(text) > 90:
        return 0
    if line.size >= body_size + 5:
        return 2
    if line.size >= body_size + 2.5:
        return 3
    return 0


def _normalize_list_marker(text: str) -> str:
    return re.sub(r"^\s*[•◦▪]\s+", "- ", text)


def _render_structured_lines(lines: list[_TextLine]) -> str:
    if not lines:
        return ""

    body_size = _body_font_size(lines)
    blocks: list[str] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(" ".join(part.strip() for part in paragraph if part.strip()))
            paragraph.clear()

    for line in lines:
        text = line.text.strip()
        plain = line.plain_text.strip()
        if not text:
            continue

        heading_level = _is_heading_candidate(line, body_size)
        if heading_level:
            flush_paragraph()
            blocks.append(f"{'#' * heading_level} {plain}")
            continue

        if _is_list_line(plain):
            flush_paragraph()
            blocks.append(_normalize_list_marker(text))
            continue

        if line.bold_ratio >= 0.8 and len(plain) <= 70:
            flush_paragraph()
            blocks.append(_markdown_bold(plain))
            continue

        paragraph.append(text)

    flush_paragraph()
    return "\n\n".join(blocks)


def _extract_structured_text(
    page: fitz.Page,
    table_bboxes: list[fitz.Rect] | None = None,
) -> str:
    """Extract block-ordered Markdown with simple heading, bold, and list inference."""
    table_bboxes = table_bboxes or []
    lines = _collect_text_lines(page, table_bboxes)
    structured = _render_structured_lines(lines)
    if structured:
        return structured
    if table_bboxes:
        return ""
    return _clean_pdf_text(page.get_text("text", sort=True))


def _extract_raw_text(page: fitz.Page, table_bboxes: list[fitz.Rect] | None = None) -> str:
    table_bboxes = table_bboxes or []
    if table_bboxes:
        lines = _collect_text_lines(page, table_bboxes)
        return _clean_pdf_text("\n".join(line.plain_text for line in lines))
    return _clean_pdf_text(page.get_text("text", sort=True))


def _table_to_markdown(rows: list[list[str | None]]) -> str:
    cleaned_rows = [
        [str(cell or "").replace("|", "\\|").replace("\n", "<br>").strip() for cell in row]
        for row in rows
    ]
    cleaned_rows = [row for row in cleaned_rows if any(cell for cell in row)]
    if not cleaned_rows:
        return ""

    column_count = max(len(row) for row in cleaned_rows)
    normalized = [row + [""] * (column_count - len(row)) for row in cleaned_rows]
    header = normalized[0]
    body = normalized[1:]

    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in range(column_count)) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _table_needs_image_fallback(rows: list[list[str | None]]) -> bool:
    if not rows:
        return True

    non_empty_rows = [row for row in rows if any(cell for cell in row)]
    if not non_empty_rows:
        return True

    widths = {len(row) for row in non_empty_rows}
    has_missing_cells = any(cell is None for row in non_empty_rows for cell in row)
    return has_missing_cells or len(widths) > 1


def _save_page_region(
    page: fitz.Page,
    bbox: tuple[float, float, float, float],
    output_path: Path,
    quality: int,
) -> None:
    clip = fitz.Rect(bbox)
    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False, clip=clip)
    with Image.open(BytesIO(pixmap.tobytes("png"))) as image:
        image.save(output_path, "WEBP", quality=quality, method=6)


def _extract_tables(
    page: fitz.Page,
    page_number: int,
    assets_dir: Path,
    quality: int,
) -> tuple[list[PDFTableResult], list[fitz.Rect]]:
    tables: list[PDFTableResult] = []
    bboxes: list[fitz.Rect] = []

    # PyMuPDF can print advisory text while finding tables; keep conversion logs clean.
    with contextlib.redirect_stdout(StringIO()), contextlib.redirect_stderr(StringIO()):
        table_finder = page.find_tables()

    for table_index, table in enumerate(table_finder.tables, start=1):
        rows = table.extract()
        markdown = _table_to_markdown(rows)
        bbox = tuple(float(value) for value in table.bbox)
        bboxes.append(fitz.Rect(table.bbox))

        asset_name = None
        warning = None
        if _table_needs_image_fallback(rows) or not markdown:
            asset_name = f"table_p{page_number:03d}_{table_index:03d}.webp"
            _save_page_region(page, bbox, assets_dir / asset_name, quality)
            warning = "Table was too irregular for reliable Markdown; saved table image fallback."
            markdown = markdown or None

        tables.append(
            PDFTableResult(
                page_number=page_number,
                markdown=markdown,
                row_count=int(table.row_count),
                col_count=int(table.col_count),
                bbox=bbox,
                asset_name=asset_name,
                warning=warning,
            )
        )

    return tables, bboxes


def _extract_links(page: fitz.Page, page_number: int) -> list[PDFLinkResult]:
    links: list[PDFLinkResult] = []
    for index, link in enumerate(page.get_links(), start=1):
        kind = int(link.get("kind", 0))
        if kind == fitz.LINK_URI and link.get("uri"):
            target = str(link["uri"])
            links.append(
                PDFLinkResult(
                    page_number=page_number,
                    label=target,
                    target=target,
                    kind="uri",
                )
            )
        elif kind == fitz.LINK_GOTO and link.get("page") is not None:
            target_page = int(link["page"]) + 1
            links.append(
                PDFLinkResult(
                    page_number=page_number,
                    label=f"Internal link {index}",
                    target=f"PDF page {target_page}",
                    kind="internal",
                )
            )
    return links


def _should_keep_image(width: int, height: int) -> bool:
    if width < 120 or height < 120:
        return False
    if width * height < 40_000:
        return False
    return True


def _save_pdf_image(
    document: fitz.Document,
    xref: int,
    output_path: Path,
    quality: int,
) -> tuple[int, int]:
    pixmap = fitz.Pixmap(document, xref)
    try:
        if pixmap.alpha or pixmap.colorspace is None or pixmap.n >= 5:
            pixmap = fitz.Pixmap(fitz.csRGB, pixmap)
        image_bytes = pixmap.tobytes("png")
    finally:
        pixmap = None

    with Image.open(BytesIO(image_bytes)) as image:
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGB")
        image.save(output_path, "WEBP", quality=quality, method=6)
        return image.width, image.height


def _save_page_render(page: fitz.Page, output_path: Path, quality: int) -> None:
    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    with Image.open(BytesIO(pixmap.tobytes("png"))) as image:
        image.save(output_path, "WEBP", quality=quality, method=6)


def process_pdf(
    input_path: str | Path,
    assets_dir: str | Path,
    quality: int = 75,
    ocr_enabled: bool = False,
    render_pages: bool = False,
) -> PDFDocumentResult:
    source = Path(input_path)
    assets = Path(assets_dir)
    assets.mkdir(parents=True, exist_ok=True)

    pages: list[PDFPageResult] = []
    saved_xrefs: dict[int, PDFImageResult] = {}

    with fitz.open(source) as document:
        for page_index, page in enumerate(document, start=1):
            page_asset_name = None
            if render_pages:
                page_asset_name = f"page_{page_index:03d}.webp"
                _save_page_render(page, assets / page_asset_name, quality)

            tables, table_bboxes = _extract_tables(page, page_index, assets, quality)
            text = _extract_structured_text(page, table_bboxes)
            raw_text = _extract_raw_text(page, table_bboxes)
            links = _extract_links(page, page_index)
            warning = None
            ocr_used = False
            images: list[PDFImageResult] = []

            for image_index, image_info in enumerate(page.get_images(full=True), start=1):
                xref = image_info[0]
                width = int(image_info[2])
                height = int(image_info[3])

                if not _should_keep_image(width, height):
                    continue

                if xref in saved_xrefs:
                    images.append(saved_xrefs[xref])
                    continue

                asset_name = f"image_p{page_index:03d}_{image_index:03d}.webp"
                output_path = assets / asset_name
                saved_width, saved_height = _save_pdf_image(document, xref, output_path, quality)
                image_result = PDFImageResult(
                    page_number=page_index,
                    asset_name=asset_name,
                    width=saved_width,
                    height=saved_height,
                    source_xref=xref,
                )
                saved_xrefs[xref] = image_result
                images.append(image_result)

            if ocr_enabled and not text:
                ocr_asset_name = page_asset_name or f"ocr_page_{page_index:03d}.webp"
                page_output_path = assets / ocr_asset_name
                if not page_output_path.exists():
                    _save_page_render(page, page_output_path, quality)
                # OCR is only attempted when the PDF has no extractable text on this page.
                result = ocr.extract_text(page_output_path)
                text = result.text
                raw_text = result.text
                warning = result.warning
                ocr_used = True

            pages.append(
                PDFPageResult(
                    page_number=page_index,
                    text=text,
                    raw_text=raw_text,
                    tables=tables,
                    images=images,
                    links=links,
                    page_asset_name=page_asset_name,
                    ocr_used=ocr_used,
                    ocr_warning=warning,
                )
            )

    asset_size_bytes = sum(path.stat().st_size for path in assets.glob("*.webp"))
    return PDFDocumentResult(
        source_size_bytes=source.stat().st_size,
        asset_size_bytes=asset_size_bytes,
        pages=pages,
    )
