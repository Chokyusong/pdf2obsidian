from __future__ import annotations

from io import BytesIO

import fitz
import pytest
from PIL import Image, ImageDraw

from pdf2obsidian.core.converter import ConversionOptions, convert_file, convert_files
from pdf2obsidian.core.lecture.ai_summarizer import AIReconstructionResult


def _sample_png_bytes() -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (240, 180), color=(40, 120, 200))
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 220, 80), fill=(20, 20, 40))
    draw.rectangle((40, 105, 180, 150), fill=(240, 120, 40))
    draw.text((52, 118), "PDF IMAGE", fill=(255, 255, 255))
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_pdf_conversion_uses_files_folder_and_manage_pdf_profile(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    output_root = tmp_path / "output"

    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 72), "Main Heading", fontsize=22)
    page.insert_image(fitz.Rect(72, 120, 312, 300), stream=_sample_png_bytes())
    document.save(pdf_path)
    document.close()

    result = convert_file(pdf_path, ConversionOptions(output_root=output_root))

    markdown = result.markdown_path.read_text(encoding="utf-8")
    expected_asset = result.output_dir / "Files" / "sample" / "p001-img01.webp"

    assert expected_asset.exists()
    assert "![[Files/sample/p001-img01.webp]]" in markdown
    assert "Conversion profile: manage-pdf-in-obsidian" in markdown
    assert "page_001.webp" not in markdown


def test_pdf_webp_compression_creates_compressed_pdf_and_report(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    output_root = tmp_path / "output"

    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 72), "Compression sample", fontsize=18)
    page.insert_image(fitz.Rect(72, 120, 312, 300), stream=_sample_png_bytes())
    document.save(pdf_path)
    document.close()

    logs: list[str] = []
    result = convert_file(
        pdf_path,
        ConversionOptions(
            output_root=output_root,
            pdf_output_format="webp_compression",
            image_quality=60,
        ),
        log=logs.append,
    )

    compressed_pdf = result.output_dir / "sample-compressed.pdf"
    report = result.output_dir / "sample-compression-report.md"

    assert result.kind == "pdf_compression"
    assert result.markdown_path == compressed_pdf
    assert compressed_pdf.exists()
    assert report.exists()
    assert "PDF Compression Report" in report.read_text(encoding="utf-8")
    assert any("PDF compression result:" in message for message in logs)
    assert any("smaller" in message for message in logs)

    with fitz.open(compressed_pdf) as compressed:
        assert compressed.page_count == 1


def test_convert_files_reports_pdf_page_progress(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    output_root = tmp_path / "output"

    document = fitz.open()
    for page_number in range(1, 4):
        page = document.new_page(width=595, height=842)
        page.insert_text((72, 72), f"Page {page_number}", fontsize=18)
    document.save(pdf_path)
    document.close()

    logs: list[str] = []
    progress_values: list[int] = []

    def progress(done: int, count: int) -> None:
        progress_values.append(int((done / count) * 100))

    convert_files(
        [pdf_path],
        ConversionOptions(output_root=output_root),
        log=logs.append,
        progress=progress,
    )

    assert any(0 < value < 100 for value in progress_values)
    assert progress_values[-1] == 100
    assert any("Processing PDF page 1/3" in message for message in logs)


def test_basic_transcript_conversion_omits_removed_optional_sections(tmp_path):
    transcript_path = tmp_path / "lecture.vtt"
    output_root = tmp_path / "output"
    transcript_path.write_text(
        "\n".join(
            [
                "WEBVTT",
                "",
                "00:00:01.000 --> 00:00:04.000",
                "오늘은 목표 설정 방법을 설명합니다.",
                "",
                "00:00:05.000 --> 00:00:08.000",
                "반드시 실행 계획을 작성하세요.",
            ]
        ),
        encoding="utf-8",
    )

    result = convert_file(transcript_path, ConversionOptions(output_root=output_root))

    markdown = result.markdown_path.read_text(encoding="utf-8")

    assert "## 복습 질문" not in markdown
    assert "## 실행 체크리스트" not in markdown
    assert "00:00" not in markdown


def test_transcript_ollama_failure_raises_instead_of_fallback(tmp_path, monkeypatch):
    transcript_path = tmp_path / "lecture.txt"
    output_root = tmp_path / "output"
    transcript_path.write_text(
        "오늘은 로컬 학습 노트를 만드는 방법을 설명합니다. 먼저 자막 파일을 준비합니다.",
        encoding="utf-8",
    )

    monkeypatch.setattr("pdf2obsidian.core.converter.is_ollama_running", lambda base_url: True)
    monkeypatch.setattr(
        "pdf2obsidian.core.converter.reconstruct_blocks_with_ollama",
        lambda *args, **kwargs: AIReconstructionResult(
            markdown="should not be saved",
            chunks=1,
            warning="Ollama reconstruction failed: model not found",
        ),
    )

    with pytest.raises(ValueError, match="Ollama reconstruction failed"):
        convert_file(
            transcript_path,
            ConversionOptions(output_root=output_root, transcript_ai_mode="ollama"),
        )

    assert not (output_root / "lecture" / "lecture.md").exists()


def test_transcript_ollama_short_output_logs_quality_warning(tmp_path, monkeypatch):
    transcript_path = tmp_path / "lecture.txt"
    output_root = tmp_path / "output"
    transcript_path.write_text("원문 보존 테스트입니다. " * 200, encoding="utf-8")

    monkeypatch.setattr("pdf2obsidian.core.converter.is_ollama_running", lambda base_url: True)
    monkeypatch.setattr(
        "pdf2obsidian.core.converter.reconstruct_blocks_with_ollama",
        lambda *args, **kwargs: AIReconstructionResult(
            markdown="---\ntitle: short\n---\n\n# short\n",
            chunks=1,
        ),
    )

    logs: list[str] = []
    convert_file(
        transcript_path,
        ConversionOptions(output_root=output_root, transcript_ai_mode="ollama"),
        log=logs.append,
    )

    assert any("less than 25%" in message for message in logs)
