from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps

from pdf2obsidian.core import ocr


@dataclass(frozen=True)
class ImageConversionResult:
    asset_name: str
    text: str = ""
    ocr_warning: str | None = None


def save_image_as_webp(
    input_path: str | Path,
    assets_dir: str | Path,
    quality: int = 75,
    output_name: str = "image_001.webp",
    ocr_enabled: bool = False,
) -> ImageConversionResult:
    source = Path(input_path)
    assets = Path(assets_dir)
    assets.mkdir(parents=True, exist_ok=True)
    output_path = assets / output_name

    with Image.open(source) as image:
        converted = ImageOps.exif_transpose(image)
        if converted.mode not in {"RGB", "RGBA"}:
            converted = converted.convert("RGB")
        converted.save(output_path, "WEBP", quality=quality, method=6)

    text = ""
    warning = None
    if ocr_enabled:
        result = ocr.extract_text(output_path)
        text = result.text
        warning = result.warning

    return ImageConversionResult(asset_name=output_name, text=text, ocr_warning=warning)
