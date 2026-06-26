from __future__ import annotations

import re
from dataclasses import dataclass

from pdf2obsidian.core.ai.ollama_client import reconstruct_with_ollama
from pdf2obsidian.core.lecture.prompt_loader import load_prompt
from pdf2obsidian.core.transcript_processor import TranscriptBlock

PRESERVATION_CHECKS = [
    (
        "RAS 시스템",
        ["RAS", "RIS", "내비게이션", "네비게이션"],
        ["RAS", "RIS", "내비게이션", "네비게이션"],
    ),
    (
        "쇼츠/SNS로 인한 정보 과부하",
        ["쇼츠", "쇼폼", "SNS", "인스타그램", "짧은 시간", "정보"],
        ["쇼츠", "쇼폼", "SNS", "인스타그램", "정보 과부하"],
    ),
    (
        "100번 쓰기",
        ["100번 쓰기", "100번"],
        ["100번 쓰기", "100번"],
    ),
    (
        "독서와 글쓰기",
        ["독서", "글쓰기"],
        ["독서", "글쓰기"],
    ),
    (
        "독서모임",
        ["독서 모임", "독서 모음"],
        ["독서모임"],
    ),
    (
        "서평",
        ["서평"],
        ["서평"],
    ),
    (
        "매일 1% 성장",
        ["1%", "37배"],
        ["1%", "37배"],
    ),
    (
        "무의식 해킹의 법칙 4단계",
        ["무의식", "4단계"],
        ["무의식", "4단계"],
    ),
    (
        "유튜브 채널 새로 만들기",
        ["유튜브", "채널"],
        ["유튜브", "채널"],
    ),
    (
        "관심 주제 채널 20~30개 구독",
        ["20", "30", "채널", "구독"],
        ["20~30", "20-30", "30", "30개"],
    ),
    (
        "많게는 100개 채널 구독",
        ["100", "채널", "구독"],
        ["100", "100개"],
    ),
    (
        "1~2일간 관련 영상만 시청",
        ["하루 이틀", "1~2", "1-2", "관련된 영상들만"],
        ["하루 이틀", "1~2", "1-2", "관련된 영상들만"],
    ),
    (
        "최소 60일 이상 환경 유지",
        ["60일", "66일"],
        ["60일", "66일"],
    ),
    (
        "멘토 레버리지",
        ["멘토", "레버리지", "버리지"],
        ["멘토", "레버리지", "버리지"],
    ),
    (
        "멘토 내용을 그대로 따라야 하는 이유",
        ["그대로 따라", "있는 그대로", "성공방정식"],
        ["그대로 따라", "있는 그대로", "성공방정식"],
    ),
    (
        "내 생각 추가 금지",
        ["내 생각", "추가 금지"],
        ["내 생각", "추가 금지"],
    ),
    (
        "최종 미션",
        ["미션", "플랜", "실행 계획"],
        ["미션", "플랜", "실행 계획"],
    ),
]


@dataclass(frozen=True)
class AIReconstructionResult:
    markdown: str
    chunks: int
    warning: str | None = None


def chunk_text(text: str, max_chars: int = 6000) -> list[str]:
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    if not paragraphs:
        paragraphs = [text.strip()] if text.strip() else []

    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for paragraph in paragraphs:
        if current and size + len(paragraph) > max_chars:
            chunks.append("\n\n".join(current))
            current = []
            size = 0
        current.append(paragraph)
        size += len(paragraph)
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def reconstruct_blocks_with_ollama(
    blocks: list[TranscriptBlock],
    title: str,
    source_type: str,
    model: str,
    source_file: str = "",
    output_language: str = "auto",
    base_url: str = "http://localhost:11434",
    max_chars: int = 24000,
) -> AIReconstructionResult:
    source_text = "\n\n".join(block.text for block in blocks if block.text.strip())
    if not source_text.strip():
        return AIReconstructionResult(
            markdown="",
            chunks=0,
            warning="No transcript text was found.",
        )

    template = _build_language_prompt(load_prompt("lecture_study_note_ko"), output_language)
    chunks = chunk_text(source_text, max_chars=max_chars)
    reconstructions = [
        reconstruct_with_ollama(chunk, model=model, template=template, base_url=base_url)
        for chunk in chunks
    ]

    failed = [
        reconstruction
        for reconstruction in reconstructions
        if reconstruction.startswith("Ollama reconstruction failed:")
    ]
    if failed:
        return AIReconstructionResult(markdown="", chunks=len(chunks), warning=failed[0])

    combined = "\n\n".join(reconstructions)
    if len(reconstructions) > 1:
        final_prompt = (
            f"{template}\n\n"
            "The following text contains partial notes from transcript chunks. "
            "Merge them into one final Markdown note. "
            "Remove duplicates, but do not reduce details. "
            "Preserve all examples, numbers, missions, and execution steps."
        )
        combined = reconstruct_with_ollama(
            combined,
            model=model,
            template=final_prompt,
            base_url=base_url,
        )
        if combined.startswith("Ollama reconstruction failed:"):
            return AIReconstructionResult(markdown="", chunks=len(chunks), warning=combined)

    markdown = _normalize_final_markdown(
        combined,
        title=title,
        source_type=source_type,
        source_file=source_file,
    )
    markdown = _append_source_preservation_addendum(markdown, source_text)
    markdown = _ensure_quality_checklist(markdown)
    return AIReconstructionResult(markdown=markdown, chunks=len(chunks))


def _normalize_final_markdown(
    markdown: str,
    title: str,
    source_type: str,
    source_file: str,
) -> str:
    content = markdown.strip()
    if not content:
        return ""

    # Some small models wrap the answer in fences. Store clean Markdown only.
    if content.startswith("```"):
        lines = content.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    if content.startswith("---"):
        return content

    return "\n".join(
        [
            "---",
            f'title: "{title}"',
            'type: lecture-note',
            'status: complete',
            f"source: {source_type}",
            f'source_file: "{source_file}"',
            "tags:",
            "  - lecture-note",
            "  - study-note",
            "  - obsidian",
            "---",
            "",
            content,
        ]
    )


def _build_language_prompt(template: str, output_language: str) -> str:
    language = output_language.lower().strip()
    if language == "ko":
        instruction = (
            "Output language: Korean. Translate and rewrite the lecture into natural Korean. "
            "Keep proper nouns, tool names, commands, and code in their original form when needed."
        )
    elif language == "en":
        instruction = (
            "Output language: English. Translate and rewrite the lecture into clear English. "
            "Keep proper nouns, tool names, commands, and code in their original form when needed."
        )
    else:
        instruction = (
            "Output language: same as source. If the source is Korean, write Korean. "
            "If the source is English, write English."
        )
    return f"{template}\n\n{instruction}"


def _ensure_quality_checklist(markdown: str) -> str:
    if "## 품질 검증" in markdown:
        return markdown
    checklist = """

---

## 품질 검증

- [ ] 강의를 보지 않아도 이해 가능한가?
- [ ] 핵심 개념이 모두 포함되었는가?
- [ ] 강의 예시가 포함되었는가?
- [ ] 숫자 데이터가 유지되었는가?
- [ ] 실행 방법이 포함되었는가?
- [ ] 미션이 포함되었는가?
- [ ] 원본 대비 과도하게 압축되지 않았는가?
"""
    return markdown.rstrip() + checklist


def _append_source_preservation_addendum(markdown: str, source_text: str) -> str:
    if "## 원문 보존 보강" in markdown:
        return markdown

    missing_sections: list[str] = []
    for label, source_terms, output_terms in PRESERVATION_CHECKS:
        if not _contains_any(source_text, source_terms):
            continue
        if _contains_any(markdown, output_terms):
            continue
        excerpts = _source_excerpts(source_text, source_terms)
        if not excerpts:
            continue
        missing_sections.append(
            "\n".join(
                [
                    f"### {label}",
                    "",
                    *[f"- {excerpt}" for excerpt in excerpts],
                ]
            )
        )

    if not missing_sections:
        return markdown

    addendum = "\n\n---\n\n## 원문 보존 보강\n\n"
    addendum += (
        "아래 항목은 생성 결과에서 누락될 수 있어 원문 문장을 기준으로 보강했습니다.\n\n"
    )
    addendum += "\n\n".join(missing_sections)
    return markdown.rstrip() + addendum


def _contains_any(text: str, terms: list[str]) -> bool:
    normalized = text.lower()
    return any(term.lower() in normalized for term in terms)


def _source_excerpts(source_text: str, terms: list[str], limit: int = 2) -> list[str]:
    fragments = [
        fragment.strip()
        for fragment in re.split(r"\n+", source_text)
        if fragment.strip()
    ]
    excerpts: list[str] = []
    seen: set[str] = set()
    for index, fragment in enumerate(fragments):
        if not _contains_any(fragment, terms):
            continue
        start = max(0, index - 1)
        end = min(len(fragments), index + 2)
        excerpt = " ".join(fragments[start:end])
        excerpt = re.sub(r"\s+", " ", excerpt).strip()
        if excerpt and excerpt not in seen:
            excerpts.append(excerpt)
            seen.add(excerpt)
        if len(excerpts) >= limit:
            break
    return excerpts
