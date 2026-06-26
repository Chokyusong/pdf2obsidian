from __future__ import annotations

from datetime import date

from pdf2obsidian.core.lecture.modes import (
    DEFAULT_AI_MODE,
    DEFAULT_OUTPUT_MODE,
    normalize_ai_mode,
    normalize_output_mode,
)
from pdf2obsidian.core.lecture.prompt_loader import load_prompt
from pdf2obsidian.core.lecture.templates import (
    LECTURE_STUDY_NOTE_SECTION_HEADINGS,
    render_lecture_study_note,
)

PRIVATE_WORD_PARTS = [
    ("와", "디즈"),
    ("블러", "리즘"),
    ("디지털", "노마드"),
    ("유", "료", "강의"),
    ("AUTO", "LED"),
    ("LLM", " Wiki"),
    ("AGENTS", ".md"),
]


def test_template_contains_required_sections_and_frontmatter():
    markdown = render_lecture_study_note(
        title="Sample lecture",
        source_type="vtt",
        overview="The lecture explains local note conversion.",
        created=date(2026, 6, 26),
    )

    assert 'type: "lecture-study-note"' in markdown
    assert 'source: "vtt"' in markdown
    for heading in LECTURE_STUDY_NOTE_SECTION_HEADINGS:
        assert heading in markdown


def test_missing_fields_do_not_crash_and_heading_order_is_stable():
    markdown = render_lecture_study_note(title="", source_type="")

    assert "Not clearly found in source." in markdown
    positions = [markdown.index(heading) for heading in LECTURE_STUDY_NOTE_SECTION_HEADINGS]
    assert positions == sorted(positions)


def test_template_and_prompts_do_not_include_private_words():
    content = "\n".join(
        [
            render_lecture_study_note(title="Sample", source_type="txt"),
            load_prompt("lecture_basic"),
            load_prompt("lecture_ollama"),
            load_prompt("lecture_openai"),
            load_prompt("output_study_note"),
        ]
    )

    for word in ("".join(parts) for parts in PRIVATE_WORD_PARTS):
        assert word not in content


def test_default_ai_mode_and_output_mode_are_separate():
    assert DEFAULT_AI_MODE == "basic"
    assert DEFAULT_OUTPUT_MODE == "study_note"
    assert normalize_ai_mode("ollama") == "ollama"
    assert normalize_output_mode("ebook") == "ebook"
    assert normalize_ai_mode("study_note") == "basic"
    assert normalize_output_mode("ollama") == "study_note"
