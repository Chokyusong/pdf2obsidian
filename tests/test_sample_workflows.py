from __future__ import annotations

from pathlib import Path

import fitz

from pdf2obsidian.core.converter import ConversionOptions, convert_file

SAMPLES_DIR = Path("docs/samples")


def test_sample_transcript_converts_to_markdown(tmp_path):
    result = convert_file(
        SAMPLES_DIR / "sample_lecture.vtt",
        ConversionOptions(output_root=tmp_path / "transcript"),
    )

    markdown = result.markdown_path.read_text(encoding="utf-8")

    assert result.kind == "transcript"
    assert result.markdown_path.exists()
    assert result.output_dir.name == "sample_lecture"
    assert "type: \"lecture-study-note\"" in markdown
    assert "sample_lecture.vtt" in markdown
    assert "## 복습 질문" not in markdown
    assert "## 실행 체크리스트" not in markdown


def test_sample_pdf_converts_to_markdown_and_webp_assets(tmp_path):
    result = convert_file(
        SAMPLES_DIR / "sample_course.pdf",
        ConversionOptions(output_root=tmp_path / "pdf-markdown"),
    )

    markdown = result.markdown_path.read_text(encoding="utf-8")
    webp_assets = list(result.output_dir.rglob("*.webp"))

    assert result.kind == "pdf"
    assert result.markdown_path.exists()
    assert result.output_dir.name == "sample_course"
    assert "Conversion profile: manage-pdf-in-obsidian" in markdown
    assert "Sample Course Pack" in markdown
    assert webp_assets
    assert any("![[Files/sample_course/" in line for line in markdown.splitlines())


def test_sample_pdf_converts_to_compressed_pdf_and_report(tmp_path):
    result = convert_file(
        SAMPLES_DIR / "sample_course.pdf",
        ConversionOptions(
            output_root=tmp_path / "pdf-compression",
            pdf_output_format="webp_compression",
            image_quality=60,
        ),
    )

    compressed_pdf = result.output_dir / "sample_course-compressed.pdf"
    report = result.output_dir / "sample_course-compression-report.md"
    report_text = report.read_text(encoding="utf-8")

    assert result.kind == "pdf_compression"
    assert result.markdown_path == compressed_pdf
    assert compressed_pdf.exists()
    assert report.exists()
    assert "PDF Compression Report" in report_text

    with fitz.open(compressed_pdf) as document:
        assert document.page_count >= 1
