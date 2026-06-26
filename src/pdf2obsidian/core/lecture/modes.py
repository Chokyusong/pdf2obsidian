from __future__ import annotations

from dataclasses import dataclass

AI_MODE_BASIC = "basic"
AI_MODE_OLLAMA = "ollama"
AI_MODE_CLOUD_FUTURE = "cloud_future"

OUTPUT_SIMPLE_NOTE = "simple_note"
OUTPUT_STUDY_NOTE = "study_note"
OUTPUT_EBOOK = "ebook"
OUTPUT_EXECUTIVE_SUMMARY = "executive_summary"

DEFAULT_AI_MODE = AI_MODE_BASIC
DEFAULT_OUTPUT_MODE = OUTPUT_STUDY_NOTE

AI_MODES = {
    AI_MODE_BASIC,
    AI_MODE_OLLAMA,
    AI_MODE_CLOUD_FUTURE,
}

OUTPUT_MODES = {
    OUTPUT_SIMPLE_NOTE,
    OUTPUT_STUDY_NOTE,
    OUTPUT_EBOOK,
    OUTPUT_EXECUTIVE_SUMMARY,
}

LEGACY_OUTPUT_ALIASES = {
    "ebook_draft": OUTPUT_EBOOK,
}


@dataclass(frozen=True)
class LectureRenderOptions:
    ai_mode: str = DEFAULT_AI_MODE
    output_mode: str = DEFAULT_OUTPUT_MODE


def normalize_ai_mode(value: str | None) -> str:
    if value in AI_MODES:
        return value
    return DEFAULT_AI_MODE


def normalize_output_mode(value: str | None) -> str:
    if value in LEGACY_OUTPUT_ALIASES:
        return LEGACY_OUTPUT_ALIASES[value]
    if value in OUTPUT_MODES:
        return value
    return DEFAULT_OUTPUT_MODE
