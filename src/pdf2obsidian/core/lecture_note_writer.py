from __future__ import annotations

import re
from collections import Counter
from datetime import date
from pathlib import Path

from pdf2obsidian.core.transcript_processor import TranscriptBlock

OUTPUT_TYPES = {
    "study_note": "lecture-study-note",
    "ebook_draft": "lecture-ebook-draft",
    "obsidian_moc": "obsidian-moc",
}

STOPWORDS = {
    "this",
    "that",
    "with",
    "from",
    "have",
    "will",
    "your",
    "그리고",
    "그래서",
    "하지만",
    "입니다",
    "있는",
    "없는",
    "하면",
    "이번",
    "강의",
    "여러분",
    "바로",
    "있습니다",
    "있겠죠",
    "오늘",
    "내용",
}

EXAMPLE_TERMS = ["예를", "예시", "사례", "예제로", "예컨대", "예시로"]
ACTION_TERMS = ["먼저", "다음", "단계", "방법", "실행", "설정", "클릭", "입력", "작성", "만들"]
CAUTION_TERMS = ["주의", "실수", "문제", "중요", "반드시", "하지 마", "안 됩니다", "위험"]


def _yaml_value(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。！？?])\s+|\n+", text)
    return [part.strip() for part in parts if part.strip()]


def _keyword_candidates(text: str, limit: int = 8) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}|[가-힣]{2,}", text)
    counter = Counter(word for word in words if word.lower() not in STOPWORDS)
    return [word for word, _ in counter.most_common(limit)]


def _derive_title(fallback_title: str, text: str) -> str:
    sentences = _sentences(text)
    if not sentences:
        return fallback_title
    first = re.sub(r"^(안녕하세요|여러분|오늘은)\s*", "", sentences[0])
    return first[:45].strip(" .") or fallback_title


def _chunk_blocks(
    blocks: list[TranscriptBlock],
    target_chars: int,
) -> list[list[TranscriptBlock]]:
    chunks: list[list[TranscriptBlock]] = []
    current: list[TranscriptBlock] = []
    size = 0

    for block in blocks:
        current.append(block)
        size += len(block.text)
        if size >= target_chars:
            chunks.append(current)
            current = []
            size = 0

    if current:
        chunks.append(current)

    return chunks


def _chunk_text(chunk: list[TranscriptBlock], preserve_level: str) -> str:
    text = " ".join(block.text for block in chunk).strip()
    sentences = _sentences(text)

    if preserve_level == "low":
        return " ".join(sentences[:5]) if sentences else text
    if preserve_level == "high":
        return "\n\n".join(block.text for block in chunk if block.text)
    return " ".join(sentences) if sentences else text


def _timestamp_heading(chunk: list[TranscriptBlock], keep_timestamps: bool, index: int) -> str:
    if keep_timestamps and chunk and chunk[0].start:
        start = chunk[0].start
        end = chunk[-1].end
        return f"### {start} - {end}" if end else f"### {start}"
    return f"### Part {index}"


def _filter_sentences(text: str, terms: list[str], limit: int = 8) -> list[str]:
    matched: list[str] = []
    for sentence in _sentences(text):
        if any(term in sentence for term in terms):
            matched.append(sentence)
        if len(matched) >= limit:
            break
    return matched


def _frontmatter(
    title: str,
    source_file: str,
    doc_type: str,
    output_format: str,
    created: date | None,
) -> list[str]:
    created_date = created or date.today()
    return [
        "---",
        f"title: {_yaml_value(title)}",
        f"source_file: {_yaml_value(source_file)}",
        f'created: "{created_date.isoformat()}"',
        f"type: {_yaml_value(doc_type)}",
        f"output_format: {_yaml_value(output_format)}",
        "---",
        "",
        f"# {title}",
        "",
    ]


def _write_section(lines: list[str], heading: str, body: list[str] | str) -> None:
    if isinstance(body, str):
        body_lines = [body] if body.strip() else []
    else:
        body_lines = [line for line in body if line.strip()]

    if not body_lines:
        return

    lines.extend([heading, ""])
    lines.extend(body_lines)
    lines.append("")


def _study_note(
    title: str,
    source_file: str,
    blocks: list[TranscriptBlock],
    full_text: str,
    keywords: list[str],
    preserve_level: str,
    keep_timestamps: bool,
    include_review_questions: bool,
    include_checklist: bool,
    created: date | None,
) -> list[str]:
    lines = _frontmatter(title, source_file, OUTPUT_TYPES["study_note"], "study_note", created)
    overview = _sentences(full_text)[:3]
    _write_section(lines, "## 강의 개요", [f"- {sentence}" for sentence in overview])

    concept_lines = []
    for keyword in keywords[:6]:
        related = _filter_sentences(full_text, [keyword], limit=1)
        if related:
            concept_lines.append(f"- **{keyword}**: {related[0]}")
        else:
            concept_lines.append(f"- **{keyword}**")
    _write_section(lines, "## 핵심 개념", concept_lines)

    chunks = _chunk_blocks(blocks, target_chars=900 if preserve_level == "low" else 1400)
    if chunks:
        lines.extend(["## 강의 흐름", ""])
        for index, chunk in enumerate(chunks, start=1):
            lines.extend(
                [
                    _timestamp_heading(chunk, keep_timestamps, index),
                    "",
                    _chunk_text(chunk, preserve_level),
                    "",
                ]
            )

    _write_section(lines, "## 예시 및 설명", _filter_sentences(full_text, EXAMPLE_TERMS))
    action_sentences = _filter_sentences(full_text, ACTION_TERMS)
    _write_section(lines, "## 실습 또는 실행 단계", action_sentences)
    _write_section(lines, "## 주의사항", _filter_sentences(full_text, CAUTION_TERMS))

    if include_review_questions and keywords:
        questions = [
            f"{index}. {keyword}의 의미를 원문 내용 기준으로 설명할 수 있는가?"
            for index, keyword in enumerate(keywords[:5], start=1)
        ]
        _write_section(lines, "## 복습 질문", questions)

    if include_checklist and action_sentences:
        checklist = [f"- [ ] {sentence}" for sentence in action_sentences[:6]]
        _write_section(lines, "## 실행 체크리스트", checklist)

    return lines


def _ebook_draft(
    title: str,
    source_file: str,
    blocks: list[TranscriptBlock],
    preserve_level: str,
    keep_timestamps: bool,
    created: date | None,
) -> list[str]:
    lines = _frontmatter(title, source_file, OUTPUT_TYPES["ebook_draft"], "ebook_draft", created)
    lines.extend(["## 원고 초안", ""])

    chunks = _chunk_blocks(blocks, target_chars=1200 if preserve_level != "high" else 1800)
    for index, chunk in enumerate(chunks, start=1):
        if keep_timestamps:
            lines.extend([_timestamp_heading(chunk, True, index), ""])
        elif len(chunks) > 1:
            lines.extend([f"## Part {index}", ""])
        lines.extend([_chunk_text(chunk, preserve_level), ""])

    return lines


def _obsidian_moc(
    title: str,
    source_file: str,
    blocks: list[TranscriptBlock],
    full_text: str,
    keywords: list[str],
    keep_timestamps: bool,
    created: date | None,
) -> list[str]:
    lines = _frontmatter(title, source_file, OUTPUT_TYPES["obsidian_moc"], "obsidian_moc", created)

    _write_section(lines, "## 주요 주제", [f"- {keyword}" for keyword in keywords[:8]])

    chunks = _chunk_blocks(blocks, target_chars=1400)
    if chunks:
        lines.extend(["## 문서 내 Heading 후보", ""])
        for index, chunk in enumerate(chunks, start=1):
            heading = _timestamp_heading(chunk, keep_timestamps, index)
            lines.append(f"- {heading.replace('### ', '')}")
        lines.append("")

    _write_section(lines, "## 노트 후보", [f"- {keyword}" for keyword in keywords[:8]])
    _write_section(lines, "## 관련 키워드 후보", [f"- {keyword}" for keyword in keywords])

    summary = _sentences(full_text)[:5]
    _write_section(lines, "## 원문 기반 요약 단서", [f"- {sentence}" for sentence in summary])
    return lines


def write_lecture_note(
    markdown_path: str | Path,
    title: str,
    source_file: str,
    blocks: list[TranscriptBlock],
    preserve_level: str = "medium",
    output_format: str = "study_note",
    keep_timestamps: bool = True,
    include_review_questions: bool = True,
    include_checklist: bool = True,
    created: date | None = None,
) -> Path:
    path = Path(markdown_path)
    full_text = " ".join(block.text for block in blocks)
    keywords = _keyword_candidates(full_text)
    note_title = _derive_title(title, full_text)
    selected_format = output_format if output_format in OUTPUT_TYPES else "study_note"

    if selected_format == "ebook_draft":
        lines = _ebook_draft(
            note_title,
            source_file,
            blocks,
            preserve_level,
            keep_timestamps,
            created,
        )
    elif selected_format == "obsidian_moc":
        lines = _obsidian_moc(
            note_title,
            source_file,
            blocks,
            full_text,
            keywords,
            keep_timestamps,
            created,
        )
    else:
        lines = _study_note(
            note_title,
            source_file,
            blocks,
            full_text,
            keywords,
            preserve_level,
            keep_timestamps,
            include_review_questions,
            include_checklist,
            created,
        )

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path
