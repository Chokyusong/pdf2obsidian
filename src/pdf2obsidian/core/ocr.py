from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OCRResult:
    text: str
    engine: str | None = None
    warning: str | None = None


def extract_text(image_path: str | Path) -> OCRResult:
    """Run optional local OCR without making OCR a hard dependency."""
    image = str(image_path)

    try:
        import easyocr  # type: ignore[import-not-found]

        reader = easyocr.Reader(["ko", "en"], gpu=False, verbose=False)
        lines = reader.readtext(image, detail=0, paragraph=True)
        text = "\n".join(line.strip() for line in lines if line.strip())
        return OCRResult(text=text, engine="easyocr")
    except ImportError:
        pass
    except Exception as exc:  # OCR should never stop the whole conversion.
        return OCRResult(text="", engine="easyocr", warning=f"EasyOCR failed: {exc}")

    try:
        import pytesseract  # type: ignore[import-not-found]

        text = pytesseract.image_to_string(image)
        return OCRResult(text=text.strip(), engine="tesseract")
    except ImportError:
        return OCRResult(
            text="",
            warning="OCR is enabled, but EasyOCR or Tesseract is not installed.",
        )
    except Exception as exc:
        return OCRResult(text="", engine="tesseract", warning=f"Tesseract OCR failed: {exc}")
