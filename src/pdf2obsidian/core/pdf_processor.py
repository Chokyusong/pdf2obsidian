from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import fitz
from PIL import Image

from pdf2obsidian.core import ocr


@dataclass(frozen=True)
class PDFPageResult:
    page_number: int
    asset_name: str
    text: str
    ocr_warning: str | None = None


def process_pdf(
    input_path: str | Path,
    assets_dir: str | Path,
    quality: int = 75,
    ocr_enabled: bool = False,
) -> list[PDFPageResult]:
    source = Path(input_path)
    assets = Path(assets_dir)
    assets.mkdir(parents=True, exist_ok=True)

    pages: list[PDFPageResult] = []

    with fitz.open(source) as document:
        for page_index, page in enumerate(document, start=1):
            asset_name = f"page_{page_index:03d}.webp"
            output_path = assets / asset_name
            text = page.get_text("text").strip()
            warning = None

            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            with Image.open(BytesIO(pixmap.tobytes("png"))) as image:
                image.save(output_path, "WEBP", quality=quality, method=6)

            if ocr_enabled and not text:
                result = ocr.extract_text(output_path)
                text = result.text
                warning = result.warning

            pages.append(
                PDFPageResult(
                    page_number=page_index,
                    asset_name=asset_name,
                    text=text,
                    ocr_warning=warning,
                )
            )

    return pages
