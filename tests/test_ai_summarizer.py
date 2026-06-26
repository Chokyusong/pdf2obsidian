from __future__ import annotations

from pdf2obsidian.core.lecture import ai_summarizer
from pdf2obsidian.core.transcript_processor import TranscriptBlock


def _blocks() -> list[TranscriptBlock]:
    return [
        TranscriptBlock("00:00:00", "00:01:00", "First concept with an example."),
        TranscriptBlock("00:01:00", "00:02:00", "Second concept with an action step."),
    ]


def test_chunking_splits_long_text():
    chunks = ai_summarizer.chunk_text("A" * 20 + "\n\n" + "B" * 20, max_chars=25)

    assert chunks == ["A" * 20, "B" * 20]


def test_mock_ollama_response_creates_study_note(monkeypatch):
    captured = {}

    def fake_reconstruction(text, model, template, base_url="http://localhost:11434", timeout=120):
        captured["template"] = template
        return """---
title: Sample
type: lecture-note
status: complete
source: vtt
tags:
  - lecture-note
---

# Sample

## 한 줄 핵심

Mocked lecture reconstruction with concepts and actions.
"""

    monkeypatch.setattr(ai_summarizer, "reconstruct_with_ollama", fake_reconstruction)

    result = ai_summarizer.reconstruct_blocks_with_ollama(
        _blocks(),
        title="Sample",
        source_type="vtt",
        model="qwen2.5:3b",
        output_language="en",
    )

    assert result.warning is None
    assert result.chunks == 1
    assert "type: lecture-note" in result.markdown
    assert "## 한 줄 핵심" in result.markdown
    assert "Mocked lecture reconstruction" in result.markdown
    assert "Output language: English" in captured["template"]


def test_ollama_failure_returns_template_without_crash(monkeypatch):
    def fake_reconstruction(text, model, template, base_url="http://localhost:11434", timeout=120):
        return "Ollama reconstruction failed: request timed out."

    monkeypatch.setattr(ai_summarizer, "reconstruct_with_ollama", fake_reconstruction)

    result = ai_summarizer.reconstruct_blocks_with_ollama(
        _blocks(),
        title="Sample",
        source_type="vtt",
        model="qwen2.5:3b",
    )

    assert result.warning == "Ollama reconstruction failed: request timed out."
    assert result.markdown == ""


def test_missing_source_preservation_terms_are_appended(monkeypatch):
    def fake_reconstruction(text, model, template, base_url="http://localhost:11434", timeout=600):
        return """---
title: Sample
type: lecture-note
status: complete
source: txt
tags:
  - lecture-note
---

# Sample

## 0. 한 줄 핵심

짧은 변환 결과입니다.
"""

    monkeypatch.setattr(ai_summarizer, "reconstruct_with_ollama", fake_reconstruction)

    blocks = [
        TranscriptBlock("", "", "RAS 시스템은 뇌의 내비게이션처럼 작동합니다."),
        TranscriptBlock("", "", "쇼츠와 SNS 때문에 짧은 시간에 정보가 너무 많이 들어옵니다."),
    ]

    result = ai_summarizer.reconstruct_blocks_with_ollama(
        blocks,
        title="Sample",
        source_type="txt",
        model="qwen2.5:3b",
    )

    assert "## 원문 보존 보강" in result.markdown
    assert "### RAS 시스템" in result.markdown
    assert "### 쇼츠/SNS로 인한 정보 과부하" in result.markdown


def test_basic_mode_existing_writer_still_outputs_source_based_text(tmp_path):
    from pdf2obsidian.core.lecture_note_writer import write_lecture_note

    output = tmp_path / "note.md"
    write_lecture_note(output, "Sample", "sample.vtt", _blocks())

    content = output.read_text(encoding="utf-8")

    assert "First concept with an example." in content
    assert "Unsupported invented claim" not in content
