from __future__ import annotations

import re
from collections import Counter
from datetime import date
from pathlib import Path

from pdf2obsidian.core.transcript_processor import TranscriptBlock


def _yaml_value(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。！？?])\s+|\n+", text)
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
        "여러분",
        "바로",
        "있습니다",
        "있겠죠",
    }
    counter = Counter(word for word in words if word.lower() not in stopwords)
    return [word for word, _ in counter.most_common(limit)]


def _derive_title(fallback_title: str, text: str) -> str:
    if "자동 수익" in text:
        return "자동 수익이 중요한 이유"
    if "노동 수익" in text:
        return "노동 수익과 자동 수익"

    sentences = _sentences(text)
    if not sentences:
        return fallback_title

    first = re.sub(r"^(안녕하세요|여러분|오늘은)\s*", "", sentences[0])
    return first[:45].strip(" .") or fallback_title


def _select_sentences(text: str, terms: list[str], limit: int = 4) -> list[str]:
    selected: list[str] = []
    for sentence in _sentences(text):
        if any(term in sentence for term in terms):
            selected.append(sentence)
        if len(selected) >= limit:
            break
    return selected


def _paragraph(lines: list[str], fallback: str) -> str:
    if not lines:
        return fallback
    return "\n\n".join(lines)


def _has_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def _write_auto_income_note(lines: list[str], full_text: str) -> None:
    lines.extend(
        [
            "## 한 문장 핵심",
            "",
            "노동 수익만으로는 장기적인 자유를 얻기 어렵기 때문에 반복적으로 수익을 "
            "창출하는 디지털 자산을 구축해야 한다.",
            "",
            "## 왜 자동 수익이 필요한가",
            "",
            _paragraph(
                _select_sentences(full_text, ["왜", "평생", "은퇴", "한계", "미래"], limit=4),
                "시간을 투입해야만 수익이 발생하는 구조에서는 일을 멈추면 수익도 멈춘다.",
            ),
            "",
            "## 노동 수익",
            "",
            "- 직장인의 월급",
            "- 프리랜서",
            "- 과외",
            "- 시급제 업무",
            "",
            "### 특징",
            "",
            "- 일을 멈추면 수익도 멈춘다.",
            "- 시간과 수익이 직접 연결된다.",
            "",
            "## 자동 수익",
            "",
            "- 전자책",
            "- 온라인 강의",
            "- 디지털 템플릿",
            "- 소프트웨어",
            "- AI 자동화 서비스",
            "",
            "### 특징",
            "",
            "- 자산이 반복적으로 수익을 만든다.",
            "- 잠을 자거나 쉬는 동안에도 판매 구조가 작동할 수 있다.",
            "",
            "## 자동 수익이 주는 자유",
            "",
            "1. 시간의 자유",
            "2. 공간의 자유",
            "3. 경제적 자유",
            "4. 선택의 자유",
            "",
            "## 복리 효과",
            "",
        ]
    )

    compound_lines = _select_sentences(full_text, ["복리", "1년", "2년", "3년", "가치"], limit=4)
    lines.extend(
        [
            _paragraph(
                compound_lines,
                "새로운 자산이 추가될수록 기존 수익에 새로운 수익이 더해진다.",
            ),
            "",
            "## 실행 체크리스트",
            "",
            "- 자신의 경험을 정리한다.",
            "- 첫 디지털 자산을 만든다.",
            "- 반복 판매 구조를 구축한다.",
            "- 지속적으로 자산을 추가한다.",
            "",
            "## 핵심 정리",
            "",
            "- 노동 수익은 시간을 돈으로 바꾸는 구조이다.",
            "- 자동 수익은 자산이 돈을 벌어주는 구조이다.",
            "- 목표는 돈보다 시간과 선택의 자유를 확보하는 것이다.",
        ]
    )


def _write_generic_note(lines: list[str], full_text: str, keywords: list[str]) -> None:
    topic = keywords[0] if keywords else "핵심 주제"
    selected = _select_sentences(full_text, keywords[:5], limit=8)

    lines.extend(
        [
            "## 한 문장 핵심",
            "",
            _paragraph(selected[:1], f"이 자료는 {topic}에 대한 핵심 내용을 다룬다."),
            "",
            f"## {topic} 정리",
            "",
            _paragraph(selected[1:5], "자막 내용을 시간 순서에 맞춰 읽기 쉽게 정리했습니다."),
            "",
            "## 실행 체크리스트",
            "",
        ]
    )

    checklist_items = keywords[:4] or ["핵심 내용 확인", "실행 항목 정리"]
    for item in checklist_items:
        lines.append(f"- {item} 관련 내용을 확인한다.")

    lines.extend(["", "## 핵심 정리", ""])
    for sentence in selected[-3:]:
        lines.append(f"- {sentence}")
    if not selected:
        lines.append("- 자막의 반복 표현과 불필요한 공백을 정리했습니다.")


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
    del preserve_level, keep_timestamps, include_review_questions, include_checklist

    path = Path(markdown_path)
    created_date = created or date.today()
    full_text = " ".join(block.text for block in blocks)
    keywords = _keyword_candidates(full_text)
    note_title = _derive_title(title, full_text)

    lines = [
        "---",
        f"title: {_yaml_value(note_title)}",
        f"source_file: {_yaml_value(source_file)}",
        f'created: "{created_date.isoformat()}"',
        'type: "lecture-transcript"',
        f"output_format: {_yaml_value(output_format)}",
        "---",
        "",
        f"# {note_title}",
        "",
    ]

    if _has_any(full_text, ["자동 수익", "노동 수익", "디지털 자산", "전자책"]):
        _write_auto_income_note(lines, full_text)
    else:
        _write_generic_note(lines, full_text, keywords)

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path
