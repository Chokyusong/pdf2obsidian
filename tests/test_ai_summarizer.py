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
    assert "## 0. 한 문장 핵심" in prompt
    assert "## 0. One Sentence Core" in prompt
    assert "## 12. 다음 액션" in prompt
    assert "## 12. Next Actions" in prompt
    assert "Do not collapse many distinct ideas into a few broad generic categories." in prompt
    assert "Fail if a long lecture is reduced to only two or three broad generic topics." in prompt
    assert "Put every meaningful numeric detail into the Numbers / Examples section" in prompt
    assert "Do not use Obsidian wiki links" in prompt
    assert "- [[ ]]" not in prompt


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


def test_short_or_incomplete_long_output_is_saved_without_quality_retry(monkeypatch):
    calls = []

    def fake_reconstruction(text, model, template, base_url="http://localhost:11434", timeout=600):
        calls.append(template)
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
    assert len(calls) == 1
    assert "범용 강의 재구성 품질 기준" not in calls[0]
    assert "짧은 변환 결과입니다." in result.markdown
    assert "## 원문 보존 보강" not in result.markdown
    assert "## 품질 검증" not in result.markdown


def test_long_source_rejects_thin_markdown_even_if_sections_exist():
    source_text = "강의 원문에는 개념, 숫자, 사례, 절차, 주의사항이 계속 이어집니다. " * 260
    thin_markdown = "# Sample\n\n" + "\n\n".join(
        f"## {index}. Section {index}\n\n짧은 요약입니다."
        for index in range(13)
    )

    issues = ai_summarizer._coverage_quality_issues(thin_markdown, source_text)

    assert issues
    assert "generated Markdown is too short" in issues[0]


def test_quality_target_brief_includes_generic_density_rules():
    source_text = "강의는 3단계 절차와 7일 실행 계획, 2개의 예시를 설명합니다. " * 120

    brief = ai_summarizer._quality_target_brief(source_text)
    count_brief = ai_summarizer._section_count_target_brief(source_text)
    coverage = ai_summarizer._source_coverage_brief(source_text)

    assert "minimum useful Markdown body length" in brief
    assert "one flow-table row per meaningful lecture turn" in brief
    assert "not Obsidian wiki links" in brief
    assert "lecture flow table rows" in count_brief
    assert "Numbers / Examples rows" in count_brief
    assert "source numeric/detail markers to review" in coverage
    assert "3단계" in coverage


def test_concept_detail_subsection_count_accepts_dash_and_dot_numbering():
    markdown = "\n".join(
        [
            "### 3-1. First concept",
            "### 3.2 Second concept",
            "### 4-1. First detail",
            "### 4.2 Second detail",
        ]
    )

    assert ai_summarizer._concept_detail_subsection_count(markdown) == 4


def test_generic_partial_section_reconstruction_assembles_requested_ranges(monkeypatch):
    calls = []

    def fake_reconstruction(text, model, template, base_url="http://localhost:11434", timeout=600):
        calls.append(template)
        if "`## 3. 핵심 개념 정리`" in template:
            return "## 3. 핵심 개념 정리\n\n### 3-1. 개념\n\n설명"
        if "`## 4. 강의 내용 상세 정리`" in template:
            return "## 4. 강의 내용 상세 정리\n\n### 4-1. 흐름\n\n설명"
        if "`## 5. 비교와 구조화 정리`" in template:
            return (
                "## 5. 비교\n\n| 구분 | 내용 |\n|---|---|\n\n"
                "## 6. 숫자\n\n| 항목 | 내용 |\n|---|---|\n| 7일 | 실행 기간 |\n\n"
            )
        if "`## 7. 실전 적용 방법`" in template:
            return "## 7. 실행\n\n1. 시작한다.\n\n## 8. 미션\n\n수행한다."
        if "`## 9. Obsidian 연결`" in template:
            return "## 9. Obsidian 연결\n\n- 관련 후보\n\n## 10. 적용\n\n적용한다."
        if "`## 11. 최종 핵심 정리`" in template:
            return (
                "## 11. 정리\n\n- 핵심\n\n## 12. 다음 액션\n\n- [ ] 실행"
            )
        return (
            "# Sample\n\n## 0. 핵심\n\n한 문장\n\n"
            "## 1. 요약\n\n요약\n\n## 2. 흐름\n\n| 순서 | 내용 |\n|---|---|"
        )

    monkeypatch.setattr(ai_summarizer, "reconstruct_with_ollama", fake_reconstruction)

    result = ai_summarizer._reconstruct_generic_partial_sections(
        "7일 실행 계획을 설명하는 강의입니다. " * 80,
        model="qwen2.5:7b",
        base_template="template",
        resolved_language="ko",
        base_url="http://localhost:11434",
    )

    assert len(calls) == 7
    assert "# Sample" in result
    assert "## 3. 핵심 개념" in result
    assert "## 12. 다음 액션" in result
    assert "[[" not in result


def test_generated_wiki_links_are_rejected_to_avoid_orphan_notes():
    markdown = "# Sample\n\n## 9. Obsidian Connections / Obsidian 연결\n\n- [[Generated Note]]"

    issues = ai_summarizer._structure_quality_issues(markdown, "짧은 원문")

    assert any("Obsidian wiki links are not allowed" in issue for issue in issues)


def test_wiki_links_are_sanitized_to_plain_text():
    markdown = "- [[Generated Note]]\n- [[Original|Alias]]"

    assert ai_summarizer._replace_wiki_links_with_plain_text(markdown) == (
        "- Generated Note\n- Alias"
    )


def test_final_normalization_removes_wiki_links_and_thinking_traces():
    markdown = """<think>
hidden reasoning
</think>
# Sample

## Analysis

Reasoning: internal chain

## 9. Obsidian 연결

- [[Generated Note]]
- [[Original|Alias]]
- [ ] [[새 노트]] 만들기
"""

    result = ai_summarizer._normalize_final_markdown(
        markdown,
        title="Sample",
        source_type="txt",
        source_file="sample.txt",
    )

    assert "[[" not in result
    assert "]]" not in result
    assert "<think>" not in result
    assert "Reasoning:" not in result
    assert "## Analysis" not in result
    assert "Generated Note" in result
    assert "Alias" in result
    assert "새 노트 만들기" in result


def test_final_normalization_strips_prompt_leak_before_actual_note():
    markdown = """# 1. PRIMARY GOAL

You are an expert lecture reconstruction assistant.

# 2. OUTPUT LANGUAGE

Use the requested output language.

# 8. FIXED MARKDOWN STRUCTURE

## Korean final structure

## 한국어 최종 구조

# 뇌자동화 세팅법의 기초

## 0. 한 문장 핵심

뇌 자동화의 핵심을 설명합니다.

## 1. 강의 전체 요약

강의 내용을 정리합니다.
"""

    result = ai_summarizer._normalize_final_markdown(
        markdown,
        title="Sample",
        source_type="txt",
        source_file="sample.txt",
        resolved_language="ko",
    )

    assert "PRIMARY GOAL" not in result
    assert "OUTPUT LANGUAGE" not in result
    assert "FIXED MARKDOWN STRUCTURE" not in result
    assert "한국어 최종 구조" not in result
    assert "# 뇌자동화 세팅법의 기초" in result
    assert "## 0. 한 문장 핵심" in result


def test_structure_rejects_prompt_leak_headings():
    markdown = "# 1. PRIMARY GOAL\n\nPrompt text\n\n# Actual\n\n## 0. One Sentence Core"

    issues = ai_summarizer._structure_quality_issues(markdown, "English source.", "en")

    assert any("prompt text leaked" in issue for issue in issues)


def test_structure_rejects_bilingual_and_wrong_language_headings():
    bilingual = "# Sample\n\n## 1. Lecture Overview / 강의 전체 요약\n\n내용"
    korean_with_english_heading = "# Sample\n\n## 1. Lecture Overview\n\n한국어 내용"
    english_with_korean_heading = "# Sample\n\n## 1. 강의 전체 요약\n\nEnglish content"

    bilingual_issues = ai_summarizer._structure_quality_issues(
        bilingual,
        "한국어 원문입니다.",
        "ko",
    )
    korean_issues = ai_summarizer._structure_quality_issues(
        korean_with_english_heading,
        "한국어 원문입니다.",
        "ko",
    )
    english_issues = ai_summarizer._structure_quality_issues(
        english_with_korean_heading,
        "English source text.",
        "en",
    )

    assert any("bilingual final headings" in issue for issue in bilingual_issues)
    assert any("Korean output must use Korean-only" in issue for issue in korean_issues)
    assert any("English output must use English-only" in issue for issue in english_issues)


def test_structure_rejects_thinking_reasoning_analysis_traces():
    markdown = "# Sample\n\n## Reasoning\n\n내부 추론입니다."

    issues = ai_summarizer._structure_quality_issues(markdown, "짧은 원문", "ko")

    assert any("thinking, reasoning, or analysis traces" in issue for issue in issues)


def test_required_skeleton_is_language_specific_without_bilingual_headings():
    korean = ai_summarizer._required_markdown_skeleton("ko")
    english = ai_summarizer._required_markdown_skeleton("en")

    assert " / " not in korean
    assert "Lecture Overview" not in korean
    assert "## 0. 한 문장 핵심" in korean
    assert " / " not in english
    assert "강의 전체 요약" not in english
    assert "## 0. One Sentence Core" in english


def test_auto_language_resolves_english_source_to_english():
    assert (
        ai_summarizer._resolve_output_language(
            "auto",
            "This lecture explains how to convert study material into markdown notes.",
        )
        == "en"
    )


def test_quality_retry_discards_thin_or_undercovered_markdown():
    issues = [
        "generated Markdown is too short for the source transcript",
        "too many source numbers or concrete details are missing",
    ]

    assert ai_summarizer._should_discard_current_markdown(issues) is True


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


def test_korean_language_mismatch_does_not_retry_in_one_shot_mode(monkeypatch):
    calls = []

    def fake_reconstruction(text, model, template, base_url="http://localhost:11434", timeout=600):
        calls.append(template)
        return "# Sample\n\n| Importance |\n|---|\n| 高 |\n\nThis is English output."

    monkeypatch.setattr(ai_summarizer, "reconstruct_with_ollama", fake_reconstruction)

    result = ai_summarizer.reconstruct_blocks_with_ollama(
        [TranscriptBlock("", "", "오늘은 한국어 강의 자막을 재구성합니다.")],
        title="Sample",
        source_type="txt",
        model="qwen2.5:3b",
        output_language="auto",
    )

    assert result.warning is None
    assert len(calls) == 1
    assert "이전 출력의 언어가 잘못되었습니다" not in calls[0]
    assert "高" not in result.markdown
    assert "높음" in result.markdown
    assert "This is English output." in result.markdown


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
