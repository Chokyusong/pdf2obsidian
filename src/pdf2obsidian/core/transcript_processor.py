from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pdf2obsidian.core.transcript_cleaner import clean_transcript_text, remove_repeated_sentences

TIMESTAMP_RE = re.compile(
    r"(?P<start>\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}|\d{1,2}:\d{2}[,.]\d{1,3})"
    r"\s*-->\s*"
    r"(?P<end>\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}|\d{1,2}:\d{2}[,.]\d{1,3})"
)


@dataclass(frozen=True)
class TranscriptBlock:
    start: str
    end: str
    text: str


def _normalize_timestamp(value: str) -> str:
    value = value.replace(",", ".")
    main = value.split(".")[0]
    parts = main.split(":")
    if len(parts) == 2:
        parts = ["00", *parts]
    return ":".join(part.zfill(2) for part in parts[:3])


def _parse_timed_blocks(content: str) -> list[TranscriptBlock]:
    lines = content.splitlines()
    blocks: list[TranscriptBlock] = []
    index = 0

    while index < len(lines):
        match = TIMESTAMP_RE.search(lines[index])
        if not match:
            index += 1
            continue

        start = _normalize_timestamp(match.group("start"))
        end = _normalize_timestamp(match.group("end"))
        index += 1
        text_lines: list[str] = []

        while index < len(lines) and lines[index].strip():
            line = lines[index].strip()
            if not line.isdigit() and not line.startswith(("NOTE", "STYLE", "REGION")):
                text_lines.append(line)
            index += 1

        cleaned_lines = remove_repeated_sentences(text_lines)
        text = clean_transcript_text(" ".join(cleaned_lines))
        if text:
            blocks.append(TranscriptBlock(start=start, end=end, text=text))

        index += 1

    return blocks


def _parse_plain_blocks(content: str) -> list[TranscriptBlock]:
    paragraphs = re.split(r"\n\s*\n", content)
    blocks: list[TranscriptBlock] = []

    for paragraph in paragraphs:
        lines = remove_repeated_sentences(paragraph.splitlines())
        text = clean_transcript_text(" ".join(lines))
        if text:
            blocks.append(TranscriptBlock(start="00:00:00", end="", text=text))

    return blocks


def _merge_short_blocks(
    blocks: list[TranscriptBlock],
    min_chars: int = 80,
) -> list[TranscriptBlock]:
    if not blocks:
        return []

    merged: list[TranscriptBlock] = []
    buffer = blocks[0]

    for block in blocks[1:]:
        if len(buffer.text) < min_chars:
            buffer = TranscriptBlock(
                start=buffer.start,
                end=block.end or buffer.end,
                text=f"{buffer.text} {block.text}".strip(),
            )
        else:
            merged.append(buffer)
            buffer = block

    merged.append(buffer)
    return merged


def read_transcript(path: str | Path) -> list[TranscriptBlock]:
    source = Path(path)
    content = source.read_text(encoding="utf-8-sig", errors="replace")

    if source.suffix.lower() in {".srt", ".vtt"}:
        blocks = _parse_timed_blocks(content)
        if blocks:
            return _merge_short_blocks(blocks)

    return _merge_short_blocks(_parse_plain_blocks(content))
