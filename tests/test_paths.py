from __future__ import annotations

from pdf2obsidian.utils.paths import (
    is_image,
    is_pdf,
    sanitize_filename,
    unique_path,
)


def test_sanitize_filename_removes_windows_unsafe_characters():
    assert sanitize_filename('bad<>:"/\\|?* name.pdf') == "bad_ name.pdf"
    assert sanitize_filename("CON") == "CON_file"
    assert sanitize_filename("...") == "untitled"


def test_extension_detection():
    assert is_pdf("sample.PDF")
    assert is_image("image.JPEG")
    assert is_image("image.webp")


def test_unique_path_adds_suffix(tmp_path):
    existing = tmp_path / "sample"
    existing.mkdir()

    assert unique_path(existing) == tmp_path / "sample_2"
