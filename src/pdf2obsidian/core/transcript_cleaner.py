from __future__ import annotations

import re

FILLER_WORDS = {
    "um",
    "uh",
    "erm",
    "like",
    "you know",
    "아",
    "어",
    "음",
    "그",
    "저",
    "뭐",
}


def normalize_spaces(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_transcript_text(text: str) -> str:
    cleaned = normalize_spaces(text)
    for filler in FILLER_WORDS:
        cleaned = re.sub(rf"(?<!\w){re.escape(filler)}(?!\w)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\s+([,.!?])", r"\1", cleaned)
    return cleaned.strip()


def remove_repeated_sentences(lines: list[str]) -> list[str]:
    result: list[str] = []
    previous = ""

    for line in lines:
        current = clean_transcript_text(line)
        if not current:
            continue
        if current == previous:
            continue
        result.append(current)
        previous = current

    return result
