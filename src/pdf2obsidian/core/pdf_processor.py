from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
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
class PDFPageResult:
    page_number: int
    text: str
    images: list[PDFImageResult]
    ocr_warning: str | None = None


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
    lines = [line.strip() for line in text.splitlines()]
    paragraphs: list[str] = []
    buffer: list[str] = []

    for line in lines:
        if not line:
            if buffer:
                paragraphs.append(" ".join(buffer).strip())
                buffer = []
            continue

        # Keep obvious headings or list items on their own line.
        if line.startswith(("-", "*", "•")) or line.endswith(":"):
            if buffer:
                paragraphs.append(" ".join(buffer).strip())
                buffer = []
            paragraphs.append(line)
            continue

        buffer.append(line)

    if buffer:
        paragraphs.append(" ".join(buffer).strip())

    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)


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


def process_pdf(
    input_path: str | Path,
    assets_dir: str | Path,
    quality: int = 75,
    ocr_enabled: bool = False,
) -> PDFDocumentResult:
    source = Path(input_path)
    assets = Path(assets_dir)
    assets.mkdir(parents=True, exist_ok=True)

    pages: list[PDFPageResult] = []
    saved_xrefs: dict[int, PDFImageResult] = {}

    with fitz.open(source) as document:
        for page_index, page in enumerate(document, start=1):
            text = _clean_pdf_text(page.get_text("text"))
            warning = None
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
                # OCR is only attempted when the PDF has no extractable text on this page.
                fallback_asset_name = f"ocr_page_{page_index:03d}.webp"
                fallback_output_path = assets / fallback_asset_name
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                with Image.open(BytesIO(pixmap.tobytes("png"))) as image:
                    image.save(fallback_output_path, "WEBP", quality=quality, method=6)
                result = ocr.extract_text(fallback_output_path)
                text = result.text
                warning = result.warning

            pages.append(
                PDFPageResult(
                    page_number=page_index,
                    text=text,
                    images=images,
                    ocr_warning=warning,
                )
            )

    asset_size_bytes = sum(path.stat().st_size for path in assets.glob("*.webp"))
    return PDFDocumentResult(
        source_size_bytes=source.stat().st_size,
        asset_size_bytes=asset_size_bytes,
        pages=pages,
    )
