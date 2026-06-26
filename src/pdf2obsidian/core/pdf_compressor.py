from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import fitz
from PIL import Image

PageProgressCallback = Callable[[int, int], None]


@dataclass(frozen=True)
class PDFCompressionResult:
    output_path: Path
    report_path: Path
    page_count: int
    source_size_bytes: int
    output_size_bytes: int
    quality: int
    dpi: int

    @property
    def size_reduction_percent(self) -> float | None:
        if self.source_size_bytes <= 0:
            return None
        return max(0.0, (1 - (self.output_size_bytes / self.source_size_bytes)) * 100)


def _page_to_compressed_jpeg(page: fitz.Page, quality: int, dpi: int) -> bytes:
    zoom = dpi / 72
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)

    with Image.open(BytesIO(pixmap.tobytes("png"))) as image:
        rgb = image.convert("RGB")

        # WebP is used as the lossy compression stage, then encoded to JPEG for PDF embedding.
        webp_buffer = BytesIO()
        rgb.save(webp_buffer, "WEBP", quality=quality, method=6)
        webp_buffer.seek(0)

        with Image.open(webp_buffer) as compressed:
            jpeg_buffer = BytesIO()
            compressed.convert("RGB").save(
                jpeg_buffer,
                "JPEG",
                quality=quality,
                optimize=True,
            )
            return jpeg_buffer.getvalue()


def _write_report(result: PDFCompressionResult) -> None:
    reduction = result.size_reduction_percent
    reduction_text = "unknown" if reduction is None else f"{reduction:.1f}%"
    lines = [
        "# PDF Compression Report",
        "",
        f"- Output PDF: `{result.output_path.name}`",
        f"- Source pages: {result.page_count}",
        f"- Quality: {result.quality}",
        f"- Render DPI: {result.dpi}",
        f"- Original PDF size: {result.source_size_bytes:,} bytes",
        f"- Compressed PDF size: {result.output_size_bytes:,} bytes",
        f"- Size reduction: {reduction_text}",
        "",
        "## Notes",
        "",
        "- This mode rasterizes each PDF page and rebuilds a compressed PDF.",
        "- Text selection, links, outlines, annotations, and form fields may not be preserved.",
        "- Use Markdown + Image output when editable Obsidian notes are needed.",
    ]
    result.report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def compress_pdf_to_webp_pdf(
    input_path: str | Path,
    output_dir: str | Path,
    quality: int = 75,
    dpi: int = 144,
    progress: PageProgressCallback | None = None,
) -> PDFCompressionResult:
    source = Path(input_path)
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    output_path = target_dir / f"{source.stem}-compressed.pdf"
    report_path = target_dir / f"{source.stem}-compression-report.md"

    page_count = 0
    output_document = fitz.open()
    try:
        with fitz.open(source) as document:
            total_pages = max(document.page_count, 1)
            for page in document:
                page_count += 1
                image_bytes = _page_to_compressed_jpeg(page, quality=quality, dpi=dpi)
                new_page = output_document.new_page(width=page.rect.width, height=page.rect.height)
                new_page.insert_image(new_page.rect, stream=image_bytes)
                if progress:
                    progress(page_count, total_pages)

        output_document.save(output_path, garbage=4, deflate=True)
    finally:
        output_document.close()

    result = PDFCompressionResult(
        output_path=output_path,
        report_path=report_path,
        page_count=page_count,
        source_size_bytes=source.stat().st_size,
        output_size_bytes=output_path.stat().st_size,
        quality=quality,
        dpi=dpi,
    )
    _write_report(result)
    return result
