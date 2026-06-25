from __future__ import annotations

import re
from collections import Counter
from datetime import date
from pathlib import Path

from pdf2obsidian.core.transcript_processor import TranscriptBlock


def _yaml_value(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。！？])\s+|\n+", text)
    return [part.strip() for part in parts if part.strip()]


def _keyword_candidates(text: str, limit: int = 8) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}|[가-힣]{2,}", text)
    stopwords = {
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
    }
    counter = Counter(word for word in words if word.lower() not in stopwords)
    return [word for word, _ in counter.most_common(limit)]


def _chunk_blocks(
    blocks: list[TranscriptBlock],
    target_chars: int = 1200,
) -> list[list[TranscriptBlock]]:
    chunks: list[list[TranscriptBlock]] = []
    current: list[TranscriptBlock] = []
    current_size = 0

    for block in blocks:
        current.append(block)
        current_size += len(block.text)
        if current_size >= target_chars:
            chunks.append(current)
            current = []
            current_size = 0

    if current:
        chunks.append(current)

    return chunks


def _section_title(index: int, chunk: list[TranscriptBlock]) -> str:
    if index == 0:
        return "도입"
    text = " ".join(block.text for block in chunk)
    keywords = _keyword_candidates(text, limit=1)
    if keywords:
        return f"핵심 주제 {index}: {keywords[0]}"
    return f"핵심 주제 {index}"


def _paragraph_for_chunk(chunk: list[TranscriptBlock], preserve_level: str) -> str:
    text = " ".join(block.text for block in chunk)
    sentences = _sentences(text)

    if preserve_level == "low":
        selected = sentences[:4]
    elif preserve_level == "high":
        selected = sentences
    else:
        selected = sentences[:8]

    return " ".join(selected) if selected else text


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
    created_date = created or date.today()
    full_text = " ".join(block.text for block in blocks)
    keywords = _keyword_candidates(full_text)
    opening_sentences = _sentences(full_text)[:3]
    chunks = _chunk_blocks(blocks)

    lines = [
        "---",
        f"title: {_yaml_value(title)}",
        f"source_file: {_yaml_value(source_file)}",
        f'created: "{created_date.isoformat()}"',
        'type: "lecture-transcript"',
        f"output_format: {_yaml_value(output_format)}",
        "---",
        "",
        f"# {title}",
        "",
        "## 1. 강의 개요",
        "",
    ]

    if opening_sentences:
        for sentence in opening_sentences:
            lines.append(f"- {sentence}")
    else:
        lines.append("- 자막 내용을 기반으로 강의 흐름을 정리합니다.")

    lines.extend(["", "## 2. 핵심 개념 정리", ""])
    for index, keyword in enumerate(keywords[:5], start=1):
        lines.extend(
            [
                f"### 개념 {index}: {keyword}",
                "",
                f"- {keyword} 관련 내용을 강의 흐름에서 확인합니다.",
                "",
            ]
        )

    lines.extend(["## 3. 강의 흐름별 상세 정리", ""])
    for index, chunk in enumerate(chunks, start=1):
        first = chunk[0]
        title_text = _section_title(index - 1, chunk)
        heading = f"### {first.start} - {title_text}" if keep_timestamps else f"### {title_text}"
        lines.extend([heading, "", _paragraph_for_chunk(chunk, preserve_level), ""])

    lines.extend(["## 4. 따라하기 단계", ""])
    for index, keyword in enumerate(keywords[:5], start=1):
        lines.append(f"{index}. {keyword}와 관련된 강의 내용을 다시 확인하고 직접 적용합니다.")
    if not keywords:
        lines.append("1. 강의 흐름별 상세 정리를 읽고 실행할 내용을 표시합니다.")

    lines.extend(["", "## 5. 실수하기 쉬운 부분", ""])
    lines.extend(
        [
            "- 자막 기반 정리는 문맥을 보존하지만 강사의 화면 조작은 포함하지 못할 수 있습니다.",
            "- 중요한 설정값이나 명령어는 원본 자료와 함께 확인합니다.",
            "- 반복 표현은 제거되었으므로 필요한 경우 원문 자막을 함께 보관합니다.",
            "",
        ]
    )

    if include_checklist:
        lines.extend(["## 6. 바로 실행할 체크리스트", ""])
        checklist_items = keywords[:5] or ["원문 자막 확인", "핵심 내용 표시", "실행 항목 정리"]
        for item in checklist_items:
            lines.append(f"- [ ] {item} 관련 실행 항목을 정리한다.")
        lines.append("")

    if include_review_questions:
        heading_number = "7" if include_checklist else "6"
        lines.extend([f"## {heading_number}. 복습 질문", ""])
        question_items = keywords[:5] or ["이 강의의 핵심 목표"]
        for index, item in enumerate(question_items, start=1):
            lines.append(f"{index}. {item}를 내 작업에 어떻게 적용할 수 있는가?")
        lines.append("")

    keyword_heading = "8" if include_checklist and include_review_questions else "7"
    lines.extend([f"## {keyword_heading}. Obsidian 연결용 키워드", ""])
    if keywords:
        for keyword in keywords:
            lines.append(f"- [[{keyword}]]")
    else:
        lines.append("- [[강의 노트]]")

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path
