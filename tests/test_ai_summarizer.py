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
    assert "## 품질 검증" not in result.markdown
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


def test_missing_source_preservation_terms_trigger_retry(monkeypatch):
    calls = []

    def fake_reconstruction(text, model, template, base_url="http://localhost:11434", timeout=600):
        calls.append(template)
        if len(calls) == 1:
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

RAS 시스템과 쇼츠/SNS로 인한 정보 과부하를 연결해 강의 흐름을 재구성합니다.
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

    assert result.warning is None
    assert len(calls) == 2
    assert "이전 출력은 원문에 있는 핵심 내용 일부를 빠뜨렸거나" in calls[1]
    assert "RAS 시스템" in result.markdown
    assert "쇼츠/SNS" in result.markdown
    assert "## 원문 보존 보강" not in result.markdown
    assert "## 품질 검증" not in result.markdown


def test_same_as_source_detects_korean_and_enforces_korean_prompt(monkeypatch):
    captured = {}

    def fake_reconstruction(text, model, template, base_url="http://localhost:11434", timeout=600):
        captured["template"] = template
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

한국어 강의 내용을 한국어로 재구성합니다.
"""

    monkeypatch.setattr(ai_summarizer, "reconstruct_with_ollama", fake_reconstruction)

    result = ai_summarizer.reconstruct_blocks_with_ollama(
        [TranscriptBlock("", "", "오늘은 한국어 강의 자막을 재구성합니다.")],
        title="Sample",
        source_type="txt",
        model="qwen2.5:3b",
        output_language="auto",
    )

    assert result.warning is None
    assert "최우선 지시: 출력 언어는 한국어입니다" in captured["template"]
    assert "중국어" in captured["template"]


def test_korean_language_mismatch_retries_before_returning(monkeypatch):
    calls = []

    def fake_reconstruction(text, model, template, base_url="http://localhost:11434", timeout=600):
        calls.append(template)
        if len(calls) == 1:
            return "# Sample\n\n| Importance |\n|---|\n| 高 |\n\nThis is English output."
        return "# Sample\n\n## 0. 한 줄 핵심\n\n한국어 원문을 한국어 학습자료로 재구성합니다."

    monkeypatch.setattr(ai_summarizer, "reconstruct_with_ollama", fake_reconstruction)

    result = ai_summarizer.reconstruct_blocks_with_ollama(
        [TranscriptBlock("", "", "오늘은 한국어 강의 자막을 재구성합니다.")],
        title="Sample",
        source_type="txt",
        model="qwen2.5:3b",
        output_language="auto",
    )

    assert result.warning is None
    assert len(calls) == 2
    assert "이전 출력의 언어가 잘못되었습니다" in calls[1]
    assert "高" not in result.markdown
    assert "한국어 학습자료" in result.markdown


def test_source_excerpts_end_at_natural_korean_boundary():
    text = (
        "혹시 여러분은 쇼츠 영상을 몇번 정도 본 것 같으신가요?\n"
        "저는 하루에도 수십번 아니 수백번도 넘게 여러 영상들을 봅니다.\n"
        "최근에는 쇼폼 시대가 되어서 짧은\n"
        "시간에도 무수히 많은 정보들이 쏟아지고 있습니다.\n"
        "우리의 뇌 속으로 말이죠."
    )

    excerpts = ai_summarizer._source_excerpts(text, ["쇼츠"], limit=1)

    assert excerpts
    assert not excerpts[0].endswith("짧은")
    assert excerpts[0].endswith(("있습니다", "있습니다.", "말이죠", "말이죠."))


def test_basic_mode_existing_writer_still_outputs_source_based_text(tmp_path):
    from pdf2obsidian.core.lecture_note_writer import write_lecture_note

    output = tmp_path / "note.md"
    write_lecture_note(output, "Sample", "sample.vtt", _blocks())

    content = output.read_text(encoding="utf-8")

    assert "First concept with an example." in content
    assert "Unsupported invented claim" not in content
