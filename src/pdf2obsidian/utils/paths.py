from __future__ import annotations

import re
from pathlib import Path

PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
TRANSCRIPT_EXTENSIONS = {".srt", ".vtt", ".txt", ".md"}
SUPPORTED_EXTENSIONS = PDF_EXTENSIONS | IMAGE_EXTENSIONS | TRANSCRIPT_EXTENSIONS

WINDOWS_RESERVED_NAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    "com1",
    "com2",
    "com3",
    "com4",
    "com5",
    "com6",
    "com7",
    "com8",
    "com9",
    "lpt1",
    "lpt2",
    "lpt3",
    "lpt4",
    "lpt5",
    "lpt6",
    "lpt7",
    "lpt8",
    "lpt9",
}


def sanitize_filename(name: str, fallback: str = "untitled") -> str:
    """Return a Windows-safe file or folder name."""
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    clean = re.sub(r"\s+", " ", clean).strip()
    clean = clean.strip(". ")
    clean = re.sub(r"_+", "_", clean)

    if not clean:
        clean = fallback

    if clean.lower() in WINDOWS_RESERVED_NAMES:
        clean = f"{clean}_file"

    return clean[:120]


def is_pdf(path: str | Path) -> bool:
    return Path(path).suffix.lower() in PDF_EXTENSIONS


def is_image(path: str | Path) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTENSIONS


def is_transcript(path: str | Path) -> bool:
    return Path(path).suffix.lower() in TRANSCRIPT_EXTENSIONS


def is_supported(path: str | Path) -> bool:
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS


def unique_path(path: Path) -> Path:
    """Return a non-existing path by adding numeric suffixes when needed."""
    if not path.exists():
        return path

    parent = path.parent
    stem = path.stem
    suffix = path.suffix
    counter = 2

    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def make_output_paths(input_path: str | Path, output_root: str | Path) -> tuple[Path, Path, Path]:
    source = Path(input_path)
    output_root_path = Path(output_root)
    base_name = sanitize_filename(source.stem)
    item_dir = unique_path(output_root_path / base_name)
    assets_dir = item_dir / "assets"
    markdown_path = item_dir / f"{base_name}.md"

    assets_dir.mkdir(parents=True, exist_ok=True)
    return item_dir, assets_dir, markdown_path
