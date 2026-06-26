from __future__ import annotations

from importlib.resources import files

from pdf2obsidian.core.lecture import ai_summarizer
from pdf2obsidian.core.lecture.prompt_loader import load_prompt
from pdf2obsidian.core.transcript_processor import TranscriptBlock

COURSE_SPECIFIC_KEYWORD_PARTS = [
    ("RAS", " 시스템"),
    ("100번", " 쓰기"),
    ("독서", "모임"),
    ("서", "평"),
    ("매일 ", "1% 성장"),
    ("무의식", " 해킹"),
    ("멘토", " 레버리지"),
    ("내 생각", " 추가 금지"),
    ("8천", "억"),
    ("스노우", "폭스"),
    ("60", "일"),
    ("66", "일"),
    ("100개", " 채널"),
]


def _blocks() -> list[TranscriptBlock]:
    return [
        TranscriptBlock("00:00:00", "00:01:00", "First concept with an example."),
        TranscriptBlock("00:01:00", "00:02:00", "Second concept with an action step."),
    ]


def test_chunking_splits_long_text():
    chunks = ai_summarizer.chunk_text("A" * 20 + "\n\n" + "B" * 20, max_chars=25)

    assert chunks == ["A" * 20, "B" * 20]


def test_universal_lecture_prompt_loads_and_is_packaged():
    prompt = load_prompt("lecture_study_note_ko")
    prompt_file = files("pdf2obsidian.prompts").joinpath("lecture_study_note_ko.txt")

    assert prompt_file.is_file()
    assert "Universal Lecture Reconstruction Prompt" in prompt
    assert "One Sentence Core / 한 문장 핵심" in prompt
    assert "Next Actions / 다음 액션" in prompt


def test_universal_lecture_prompt_has_no_course_specific_keywords():
    prompt = load_prompt("lecture_study_note_ko")

    for keyword in ("".join(parts) for parts in COURSE_SPECIFIC_KEYWORD_PARTS):
        assert keyword not in prompt


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


def test_short_or_incomplete_long_output_triggers_generic_quality_retry(monkeypatch):
    calls = []
    detailed_sections = "\n\n".join(
        f"## {index}. Section {index} / 섹션 {index}\n\n"
        "원문에 나온 개념, 숫자, 사례, 실행 절차를 바탕으로 학습자가 바로 적용할 수 "
        "있도록 충분히 자세히 정리합니다. "
        "데이터 백업 절차와 3-2-1 백업 원칙, 복구 테스트의 이유를 연결해서 설명합니다."
        for index in range(13)
    )

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
        return f"""---
title: Sample
type: lecture-note
status: complete
source: txt
tags:
  - lecture-note
---

# Sample

{detailed_sections}
"""

    monkeypatch.setattr(ai_summarizer, "reconstruct_with_ollama", fake_reconstruction)

    blocks = [
        TranscriptBlock(
            "",
            "",
            "데이터 백업 강의입니다. 3-2-1 백업 원칙, 주간 복구 테스트, "
            "장애 대응 체크리스트를 설명합니다. " * 25,
        ),
    ]

    result = ai_summarizer.reconstruct_blocks_with_ollama(
        blocks,
        title="Sample",
        source_type="txt",
        model="qwen2.5:3b",
    )

    assert result.warning is None
    assert len(calls) == 2
    assert "범용 강의 재구성 품질 기준" in calls[1]
    assert "generated Markdown is too short" in calls[1]
    assert "데이터 백업" in result.markdown
    assert "3-2-1 백업 원칙" in result.markdown
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
