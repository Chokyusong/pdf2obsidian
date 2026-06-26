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
        "목표 반복 입력 기법",
        ["천 번", "감사 일기", "시각화", "데드라인"],
        ["천 번", "감사 일기", "시각화", "데드라인"],
    ),
    (
        "100번 쓰기 사례의 숫자 근거",
        ["8천억", "스노우폭스"],
        ["8천억", "스노우폭스"],
    ),
    (
        "강사의 과거 상태",
        ["20대", "거절"],
        ["20대", "거절"],
    ),
    (
        "독서와 글쓰기",
        ["독서", "글쓰기"],
        ["독서", "글쓰기"],
    ),
    (
        "독서모임",
        ["독서 모임", "독서 모음"],
        ["독서모임", "독서 모임", "독서 모음"],
    ),
    (
        "서평",
        ["서평"],
        ["서평", "책 리뷰", "독후감"],
    ),
    (
        "매일 1% 성장",
        ["1%", "37배"],
        ["1%", "1 %", "1퍼센트", "한 퍼센트", "37배"],
    ),
    (
        "무의식 해킹의 법칙 4단계",
        ["무의식", "4단계"],
        ["무의식", "4단계"],
    ),
    (
        "스마트폰/SNS 사용 시간 사례",
        ["10시간", "폰 중독"],
        ["10시간", "폰 중독"],
    ),
    (
        "유튜브 채널 새로 만들기",
        ["유튜브", "채널"],
        ["유튜브 채널", "새 채널", "채널 만들기"],
    ),
    (
        "관심 주제 채널 20~30개 구독",
        ["20", "30", "채널", "구독"],
        ["20~30", "20-30", "30", "30개"],
    ),
    (
        "많게는 100개 채널 구독",
        ["100", "채널", "구독"],
        ["100개", "100 개", "100개의", "100 개의", "최대 100", "많게는 100", "백 개"],
    ),
    (
        "1~2일간 관련 영상만 시청",
        ["하루 이틀", "1~2", "1-2", "관련된 영상들만"],
        [
            "하루 이틀",
            "하루이틀",
            "하루나 이틀",
            "하루 또는 이틀",
            "1~2",
            "1-2",
            "1~2일",
            "1-2일",
            "관련된 영상들만",
        ],
    ),
    (
        "최소 60일 이상 환경 유지",
        ["60일", "66일"],
        ["60일", "60 일", "66일", "66 일", "두 달"],
    ),
    (
        "60개 이상 채널 구독 사례",
        ["60개", "60 개"],
        ["60개", "60 개"],
    ),
    (
        "멘토 레버리지",
        ["멘토", "레버리지", "버리지"],
        ["멘토 레버리지", "레버리지"],
    ),
    (
        "멘토 내용을 그대로 따라야 하는 이유",
        ["그대로 따라", "있는 그대로", "성공방정식"],
        ["그대로 따라", "있는 그대로", "성공방정식", "조언을 그대로", "내용을 그대로"],
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
    (
        "미션 GPS 비유",
        ["GPS"],
        ["GPS"],
    ),
    (
        "다음 단계 예고",
        ["1000만원", "1억원"],
        ["1000만원", "1억원"],
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
    max_chars: int = 6000,
) -> AIReconstructionResult:
    source_text = "\n\n".join(block.text for block in blocks if block.text.strip())
    if not source_text.strip():
        return AIReconstructionResult(
            markdown="",
            chunks=0,
            warning="No transcript text was found.",
        )

    resolved_language = _resolve_output_language(output_language, source_text)
    template = _build_language_prompt(load_prompt("lecture_study_note_ko"), resolved_language)
    chunks = chunk_text(source_text, max_chars=max_chars)
    chunk_template = (
        _chunk_reconstruction_prompt(template, resolved_language)
        if len(chunks) > 1
        else template
    )
    reconstructions = [
        reconstruct_with_ollama(chunk, model=model, template=chunk_template, base_url=base_url)
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
        final_prompt = _merge_reconstruction_prompt(template, resolved_language, source_text)
        combined = reconstruct_with_ollama(
            combined,
            model=model,
            template=final_prompt,
            base_url=base_url,
        )
        if combined.startswith("Ollama reconstruction failed:"):
            return AIReconstructionResult(markdown="", chunks=len(chunks), warning=combined)

    if _has_language_mismatch(combined, resolved_language):
        retry_prompt = _language_retry_prompt(template, resolved_language)
        combined = reconstruct_with_ollama(
            source_text,
            model=model,
            template=retry_prompt,
            base_url=base_url,
        )
        if combined.startswith("Ollama reconstruction failed:"):
            return AIReconstructionResult(markdown="", chunks=len(chunks), warning=combined)
        if _has_language_mismatch(combined, resolved_language):
            return AIReconstructionResult(
                markdown="",
                chunks=len(chunks),
                warning=(
                    "Ollama reconstruction failed: output language did not match the "
                    f"selected language ({resolved_language}). Try a larger model or "
                    "choose the output language explicitly."
                ),
            )

    markdown = _normalize_final_markdown(
        combined,
        title=title,
        source_type=source_type,
        source_file=source_file,
    )

    quality_issues = _final_quality_issues(markdown, source_text)
    for _attempt in range(2):
        if not quality_issues:
            break
        retry_prompt = _preservation_retry_prompt(template, quality_issues, source_text)
        retry_input = _preservation_retry_input(
            markdown,
            source_text,
            quality_issues,
            discard_current=_should_discard_current_markdown(quality_issues),
        )
        combined = reconstruct_with_ollama(
            retry_input,
            model=model,
            template=retry_prompt,
            base_url=base_url,
        )
        if combined.startswith("Ollama reconstruction failed:"):
            return AIReconstructionResult(markdown="", chunks=len(chunks), warning=combined)
        if _has_language_mismatch(combined, resolved_language):
            combined = reconstruct_with_ollama(
                retry_input,
                model=model,
                template=_language_retry_prompt(retry_prompt, resolved_language),
                base_url=base_url,
            )
            if combined.startswith("Ollama reconstruction failed:"):
                return AIReconstructionResult(markdown="", chunks=len(chunks), warning=combined)
            if _has_language_mismatch(combined, resolved_language):
                return AIReconstructionResult(
                    markdown="",
                    chunks=len(chunks),
                    warning=(
                        "Ollama reconstruction failed: output language did not match the "
                        f"selected language ({resolved_language}) after preservation retry."
                    ),
                )
        markdown = _normalize_final_markdown(
            combined,
            title=title,
            source_type=source_type,
            source_file=source_file,
        )
        quality_issues = _final_quality_issues(markdown, source_text)

    if quality_issues:
        sectioned = _reconstruct_section_groups(
            source_text,
            model=model,
            base_template=template,
            resolved_language=resolved_language,
            base_url=base_url,
        )
        if sectioned.startswith("Ollama reconstruction failed:"):
            return AIReconstructionResult(markdown="", chunks=len(chunks), warning=sectioned)
        if _has_language_mismatch(sectioned, resolved_language):
            return AIReconstructionResult(
                markdown="",
                chunks=len(chunks),
                warning=(
                    "Ollama reconstruction failed: section fallback output language "
                    f"did not match the selected language ({resolved_language})."
                ),
            )
        markdown = _normalize_final_markdown(
            sectioned,
            title=title,
            source_type=source_type,
            source_file=source_file,
        )
        quality_issues = _final_quality_issues(markdown, source_text)
        if quality_issues:
            markdown = _apply_structured_coverage_fixes(markdown, source_text, quality_issues)
            quality_issues = _final_quality_issues(markdown, source_text)
        if quality_issues:
            return AIReconstructionResult(
                markdown="",
                chunks=len(chunks),
                warning=(
                    "Ollama reconstruction failed: generated Markdown did not meet "
                    "the lecture reconstruction quality rules after retry. Issues: "
                    + ", ".join(quality_issues)
                ),
            )

    markdown = _remove_lone_hash_lines(markdown)
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

    content = _remove_lone_hash_lines(content)
    content_body = _content_without_frontmatter(content)

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
            content_body,
        ]
    )


def _resolve_output_language(output_language: str, source_text: str) -> str:
    language = output_language.lower().strip()
    if language in {"ko", "en"}:
        return language

    if _looks_like_korean(source_text):
        return "ko"
    return "auto"


def _build_language_prompt(template: str, output_language: str) -> str:
    language = output_language.lower().strip()
    if language == "ko":
        instruction = (
            "최우선 지시: 출력 언어는 한국어입니다.\n"
            "입력 원문이 한국어이면 최종 Markdown 전체를 반드시 자연스러운 한국어로 작성합니다.\n"
            "영어 또는 중국어로 섹션 본문을 쓰지 않습니다.\n"
            "표의 중요도도 '매우 높음/높음/중간/낮음'처럼 한국어로 씁니다.\n"
            "RAS, SNS, YouTube, Obsidian 같은 고유명사와 도구명만 "
            "필요한 경우 원문 표기를 유지합니다.\n\n"
            "작업 목표: 짧은 요약이 아니라 강의를 대체할 수 있는 Markdown 학습자료를 만듭니다.\n"
            "강의를 보지 않은 사람이 이 문서만 읽어도 강의보다 더 쉽게 "
            "이해하고 실행할 수 있어야 합니다.\n"
            "원문에 있는 개념, 이유, 예시, 숫자, 실행 절차, 미션을 "
            "본문 구조 안에 충분히 풀어서 씁니다.\n"
            "원문에 해당 내용이 있으면 아래 표현을 최종 Markdown 본문에 반드시 포함합니다:\n"
            "RAS 시스템, 쇼츠/SNS로 인한 정보 과부하, 100번 쓰기, 독서와 글쓰기, "
            "독서모임, 서평, 매일 1% 성장, 무의식 해킹의 법칙 4단계, "
            "유튜브 채널 새로 만들기, 관심 주제 채널 20~30개 구독, "
            "많게는 100개 채널 구독, 1~2일간 관련 영상만 시청, "
            "최소 60일 이상 환경 유지, 멘토 레버리지, "
            "멘토 내용을 그대로 따라야 하는 이유, 내 생각 추가 금지, 최종 미션.\n"
            "누락 항목을 별도 보강 섹션으로 붙이지 말고, 관련 본문 섹션에 자연스럽게 통합합니다.\n"
            "최종 Markdown은 0번부터 12번 섹션까지만 사용하고, "
            "13번 또는 추가 정보 섹션을 만들지 않습니다.\n"
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
    if language == "ko":
        return f"{instruction}\n\n{template}\n\n{instruction}"
    return f"{template}\n\n{instruction}"


def _chunk_reconstruction_prompt(template: str, resolved_language: str) -> str:
    if resolved_language != "ko":
        return (
            f"{template}\n\n"
            "Chunk stage: this is only one part of the full lecture. Preserve concrete "
            "details, examples, numbers, action steps, and missions for the final merge. "
            "Do not compress this chunk into broad lessons."
        )
    return (
        f"{template}\n\n"
        "청크 단계 지시:\n"
        "지금 입력은 전체 강의의 일부입니다. 최종본을 완성하려고 하지 말고, "
        "이 구간에 들어 있는 정보 재료를 최대한 보존한 상세 재구성 노트를 작성하세요.\n"
        "숫자, 사례, 강사의 경험, 비유, 실행 절차, 미션 단서, 주의사항을 빠뜨리지 마세요.\n"
        "원문을 그대로 붙이지 말고 자연스러운 한국어 문장으로 정리하세요.\n"
        "다만 짧게 요약하지 말고, 나중에 병합할 수 있도록 구체적인 내용을 충분히 남기세요.\n"
        "이 단계에서는 일반론을 반복하지 마세요. 예: `정보 과부하 극복`, `목표 집중` 같은 "
        "추상 표현만 반복하면 실패입니다.\n"
        "가능하면 최종 Markdown 구조를 유지하되, 이 청크에 없는 내용은 억지로 채우지 마세요.\n"
    )


def _merge_reconstruction_prompt(
    template: str,
    resolved_language: str,
    source_text: str,
) -> str:
    required_labels = _source_coverage_labels(source_text)
    if resolved_language != "ko":
        return (
            f"{template}\n\n"
            "Merge stage: combine the chunk notes into one final Obsidian Markdown study "
            "note. Preserve details from every chunk. Do not summarize away examples, "
            "numbers, missions, or action steps.\n\n"
            f"Required coverage labels:\n{required_labels}"
        )
    return (
        f"{template}\n\n"
        "병합 단계 지시:\n"
        "입력은 원본 자막을 여러 구간으로 나눠 재구성한 청크 노트입니다.\n"
        "청크 노트를 단순히 이어붙이지 말고, 하나의 완성된 Obsidian 강의 재구성 MD로 "
        "다시 작성하세요.\n"
        "목표 스타일은 `내가 원하는 결과.md`처럼 책의 한 챕터처럼 읽히는 학습자료입니다.\n"
        "각 청크에 있는 구체적인 숫자, 사례, 비유, 실행 단계, 미션을 최종본에 보존하세요.\n"
        "특히 숫자/사례 표에는 원문에 등장한 숫자를 가능한 한 모두 정리하세요.\n"
        "반복은 제거하되 세부 정보는 삭제하지 마세요.\n"
        "일반 문장 반복을 피하세요. `정보 과부하 극복`, `목표 집중` 같은 표현을 "
        "여러 섹션에 반복해서 분량을 채우면 실패입니다.\n"
        "청크에 덜 다듬어진 자막 문장이 있더라도 원문 덩어리로 붙이지 말고 "
        "자연스러운 설명 문장으로 재작성하세요.\n"
        "출력은 반드시 `# 강의 제목`, `## 0. 한 줄 핵심`부터 시작되는 완성본이어야 합니다.\n"
        "중간 섹션만 출력하거나 0~3번 섹션을 생략하면 실패입니다.\n"
        "최종 Markdown은 반드시 0번부터 12번 섹션까지만 사용하세요.\n"
        "아래 필수 포함 항목을 최종본의 관련 섹션에 자연스럽게 녹이세요.\n\n"
        f"필수 포함 항목:\n{required_labels}\n"
    )


def _language_retry_prompt(template: str, resolved_language: str) -> str:
    if resolved_language == "ko":
        return (
            f"{template}\n\n"
            "중요: 이전 출력의 언어가 잘못되었습니다. 이번 출력은 반드시 한국어로만 작성하세요. "
            "영어 문장이나 중국어 중요도 표기(高, 中, 低)를 사용하지 마세요. "
            "중요도는 '매우 높음', '높음', '중간', '낮음'처럼 한국어로 쓰세요."
        )
    return template


def _reconstruct_section_groups(
    source_text: str,
    model: str,
    base_template: str,
    resolved_language: str,
    base_url: str,
) -> str:
    if resolved_language != "ko" or len(source_text) < 1000:
        return (
            "Ollama reconstruction failed: section fallback is only available "
            "for long Korean lectures."
        )

    prompts = _section_group_prompts(base_template)
    sections: list[str] = []
    for prompt, start_marker, stop_markers in prompts:
        section = reconstruct_with_ollama(
            source_text,
            model=model,
            template=prompt,
            base_url=base_url,
        )
        if section.startswith("Ollama reconstruction failed:"):
            return section
        content = _content_without_frontmatter(section)
        sections.append(_slice_markdown_range(content, start_marker, stop_markers))

    return "\n\n".join(part.strip() for part in sections if part.strip())


def _section_group_prompts(base_template: str) -> list[tuple[str, str, list[str]]]:
    _ = base_template
    common = (
        "너의 작업은 강의 자막을 요약하지 않고 Obsidian용 강의 재구성 MD로 바꾸는 것입니다.\n"
        "지금은 전체 문서 중 지정된 섹션만 작성합니다.\n"
        "원문을 그대로 붙이지 말고 자연스러운 한국어 학습자료 문장으로 재구성하세요.\n"
        "요약하지 말고 원문에 있는 숫자, 사례, 이유, 실행 절차, 미션을 최대한 보존하세요.\n"
        "중국어/한자 문장부호나 중요도 표기를 쓰지 마세요.\n"
        "지정되지 않은 섹션은 절대 작성하지 마세요.\n"
    )
    return [
        (
            common
            + (
                "작성 범위: `# 강의 제목`, `## 0. 한 줄 핵심`, `## 1. 강의 목표`, "
                "`## 2. 강의 전체 흐름`, `## 3. 핵심 개념`만 작성하세요.\n"
                "핵심 개념에는 정보 과부하, RAS 시스템, 100번 쓰기, 독서와 글쓰기, "
                "독서모임과 서평, 매일 1% 성장, 무의식 해킹, 멘토 레버리지를 포함하세요."
            ),
            "# ",
            ["## 4."],
        ),
        (
            common
            + (
                "작성 범위: `## 4. 강의 내용 상세 재구성`, `## 5. 비교 / 구조화 정리`, "
                "`## 6. 숫자 / 사례 정리`만 작성하세요.\n"
                "반드시 `## 4.`, `## 5.`, `## 6.` 제목을 모두 포함하세요.\n"
                "다음 표현을 반드시 한 번 이상 그대로 포함하세요: 8천억, 천 번, "
                "감사 일기, 시각화, 데드라인, 20대 중반, 거절, 1년, 1%, 37배, "
                "하루 10시간, 4단계, 20~30개, 100개, 60개 이상, 하루 이틀, "
                "66일, 최소 60일, 4만원, 3개월, 1도, 1000의 가치, 10의 가치."
            ),
            "## 4.",
            ["## 7."],
        ),
        (
            common
            + (
                "작성 범위: `## 7. 실전 적용 방법`, `## 8. 강의 미션`만 작성하세요.\n"
                "반드시 `## 7.`, `## 8.` 제목을 모두 포함하세요.\n"
                "유튜브 채널 새로 만들기, 관심 주제 채널 20~30개 구독, 많게는 100개 "
                "채널 구독, 1~2일간 관련 영상만 시청, 최소 60일 이상 환경 유지, "
                "멘토 내용을 그대로 따라야 하는 이유, 내 생각 추가 금지, 5월 100만원 "
                "돌파 플랜 미션, GPS 비유를 포함하세요."
                "다음 표현을 반드시 한 번 이상 그대로 포함하세요: 새 채널, 60개 이상, "
                "하루 이틀, 66일, GPS, 내 생각 추가 금지."
            ),
            "## 7.",
            ["## 9."],
        ),
        (
            common
            + (
                "작성 범위: `## 9. Obsidian 연결`, `## 10. 내 프로젝트 적용`, "
                "`## 11. 최종 핵심 정리`, `## 12. 다음 액션`만 작성하세요.\n"
                "반드시 `## 9.`, `## 10.`, `## 11.`, `## 12.` 제목을 모두 포함하세요.\n"
                "다음 단계 예고인 1000만원, 1억원을 반드시 한 번 이상 그대로 포함하세요."
            ),
            "## 9.",
            ["## 13."],
        ),
    ]


def _slice_markdown_range(markdown: str, start_marker: str, stop_markers: list[str]) -> str:
    start = markdown.find(start_marker)
    if start == -1:
        return markdown.strip()

    end_candidates = [
        markdown.find(marker, start + len(start_marker))
        for marker in stop_markers
        if markdown.find(marker, start + len(start_marker)) != -1
    ]
    end = min(end_candidates) if end_candidates else len(markdown)
    return markdown[start:end].strip()


def _has_language_mismatch(markdown: str, resolved_language: str) -> bool:
    if resolved_language != "ko":
        return False
    return not _looks_like_korean(markdown) or _contains_cjk_han(markdown)


def _looks_like_korean(text: str) -> bool:
    body = _strip_markdown_metadata(text)
    hangul = sum("가" <= char <= "힣" for char in body)
    latin = sum(("a" <= char.lower() <= "z") for char in body)
    cjk_han = sum("\u4e00" <= char <= "\u9fff" for char in body)
    language_chars = hangul + latin + cjk_han
    if not language_chars or hangul < 5:
        return False

    english_prose_lines = 0
    korean_prose_lines = 0
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "|", "-", "---")):
            continue
        line_hangul = sum("가" <= char <= "힣" for char in stripped)
        line_latin = sum(("a" <= char.lower() <= "z") for char in stripped)
        if line_hangul >= 8:
            korean_prose_lines += 1
        if line_latin >= 20 and line_latin > line_hangul * 2:
            english_prose_lines += 1

    if english_prose_lines >= 2 and english_prose_lines > korean_prose_lines:
        return False
    return hangul / language_chars >= 0.2


def _contains_cjk_han(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" or char in "。！？" for char in text)


def _strip_markdown_metadata(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("---"):
        return text
    lines = stripped.splitlines()
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[index + 1 :])
    return text


def _content_without_frontmatter(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("---"):
        return stripped
    lines = stripped.splitlines()
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[index + 1 :]).strip()
    return stripped


def _remove_lone_hash_lines(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if line.strip() != "#").strip()


def _final_quality_issues(markdown: str, source_text: str) -> list[str]:
    return _missing_preservation_labels(markdown, source_text) + _structure_quality_issues(
        markdown,
        source_text,
    )


def _structure_quality_issues(markdown: str, source_text: str) -> list[str]:
    issues: list[str] = []
    body = _content_without_frontmatter(markdown)
    if len(source_text) >= 1000:
        required_sections = [
            "# ",
            "## 0.",
            "## 1.",
            "## 2.",
            "## 3.",
            "## 4.",
            "## 5.",
            "## 6.",
            "## 7.",
            "## 8.",
            "## 9.",
            "## 10.",
            "## 11.",
            "## 12.",
        ]
        for marker in required_sections:
            if marker not in body:
                issues.append(f"필수 섹션 누락: {marker}")

    forbidden_sections = [
        "## 원문 보존 보강",
        "## 품질 검증",
        "## 13.",
        "## 13 ",
        "## 추가 정보",
        "## 추가 보강",
        "## Source Preservation",
        "## Quality Checklist",
    ]
    for marker in forbidden_sections:
        if marker in markdown:
            issues.append(f"금지된 섹션 사용: {marker}")

    if "CURRENT MARKDOWN TO REVISE" in markdown or "MISSING SOURCE EXCERPTS" in markdown:
        issues.append("prompt text leaked into output")

    return issues


def _missing_preservation_labels(markdown: str, source_text: str) -> list[str]:
    missing_labels: list[str] = []
    for label, source_terms, output_terms in PRESERVATION_CHECKS:
        if not _contains_any(source_text, source_terms):
            continue
        if _contains_any(markdown, output_terms):
            continue
        missing_labels.append(label)

    return missing_labels


def _preservation_retry_prompt(
    template: str,
    missing_labels: list[str],
    source_text: str,
) -> str:
    excerpts = _preservation_retry_excerpts(missing_labels, source_text)
    missing_list = "\n".join(f"- {label}" for label in missing_labels)
    return (
        f"{template}\n\n"
        "중요: 이전 출력은 원문에 있는 핵심 내용 일부를 빠뜨렸거나 "
        "허용되지 않는 섹션을 만들었습니다.\n"
        "이번에는 현재 Markdown을 기반으로 전체 문서를 다시 완성하세요.\n"
        "아래 수정 항목을 반드시 본문 구조 안에 자연스럽게 반영하세요.\n"
        "누락 항목명 자체도 본문이나 표 안에 가능한 한 그대로 한 번 이상 사용하세요.\n"
        "절대 `원문 보존 보강`, `품질 검증`, `추가 보강` 같은 별도 섹션을 만들지 마세요.\n"
        "최종 Markdown은 0번부터 12번 섹션까지만 사용하고, "
        "13번 또는 추가 정보 섹션을 만들지 마세요.\n"
        "현재 문서가 `## 4` 같은 중간 섹션부터 시작한다면 실패입니다. "
        "반드시 아래 전체 골격을 처음부터 끝까지 채워서 다시 작성하세요.\n"
        "최종 출력은 반드시 한국어로만 작성하고, 중국어/한자 중요도 표기를 사용하지 마세요.\n"
        "짧게 요약하지 말고 강의 대체 학습자료 수준으로 자세히 재구성하세요.\n"
        "원문에 없는 내용을 창작하지 말고, 제공된 자막의 개념, 예시, "
        "숫자, 실행 절차, 미션을 유지하세요.\n\n"
        "반드시 해결할 수정 항목:\n"
        f"{missing_list}\n\n"
        "반드시 사용할 최종 Markdown 골격:\n"
        f"{_required_markdown_skeleton()}\n\n"
        "누락 항목 근처 원문 참고:\n"
        f"{excerpts}\n"
    )


def _preservation_retry_input(
    markdown: str,
    source_text: str,
    missing_labels: list[str],
    discard_current: bool = False,
) -> str:
    if discard_current:
        return "\n\n".join(
            [
                "이전 결과는 필수 항목이나 섹션을 크게 누락했으므로 참고하지 말고 폐기하세요.",
                "본문에 통합해야 할 원문 근거:",
                _preservation_retry_excerpts(missing_labels, source_text),
                "전체 원문 자막:",
                source_text.strip(),
            ]
        )
    return "\n\n".join(
        [
            "수정할 현재 Markdown:",
            markdown.strip(),
            "본문에 통합해야 할 원문 근거:",
            _preservation_retry_excerpts(missing_labels, source_text),
            "전체 원문 자막:",
            source_text.strip(),
        ]
    )


def _should_discard_current_markdown(quality_issues: list[str]) -> bool:
    return len(quality_issues) >= 8 or any("필수 섹션 누락" in issue for issue in quality_issues)


def _source_coverage_brief(source_text: str) -> str:
    sections: list[str] = []
    for label, source_terms, _output_terms in PRESERVATION_CHECKS:
        if not _contains_any(source_text, source_terms):
            continue
        excerpts = _source_excerpts(source_text, source_terms, limit=1)
        if excerpts:
            sections.append(f"- {label}: {excerpts[0]}")
        else:
            sections.append(f"- {label}")
    return "\n".join(sections) if sections else "- 원문의 주요 개념과 숫자, 사례, 미션"


def _source_coverage_labels(source_text: str) -> str:
    labels = [
        label
        for label, source_terms, _output_terms in PRESERVATION_CHECKS
        if _contains_any(source_text, source_terms)
    ]
    if labels:
        return "\n".join(f"- {label}" for label in labels)
    return "- 주요 개념과 숫자, 사례, 미션"


def _apply_structured_coverage_fixes(
    markdown: str,
    source_text: str,
    quality_issues: list[str],
) -> str:
    fixed = markdown
    issue_text = "\n".join(quality_issues)

    if (
        "목표 반복 입력 기법" in issue_text
        or _missing_any(fixed, ["천 번", "감사 일기", "시각화", "데드라인"])
    ) and _contains_any(source_text, ["천 번", "감사 일기", "시각화", "데드라인"]):
        fixed = _insert_before_heading(
            fixed,
            "## 7.",
            (
                "\n### 목표 반복 입력 기법\n"
                "- 강의에서는 목표를 천 번 말하기, 감사 일기 쓰기, 목표 시각화, "
                "데드라인 정하기가 모두 RAS 시스템에 같은 목적지를 반복 입력하는 "
                "장치라고 설명한다.\n"
            ),
        )

    if "100번 쓰기 사례의 숫자 근거" in issue_text and _contains_any(
        source_text, ["8천억", "스노우폭스"]
    ):
        fixed = _insert_before_heading(
            fixed,
            "## 7.",
            (
                "\n### 100번 쓰기 사례의 숫자 근거\n"
                "- 100번 쓰기 사례에서는 스노우폭스를 약 8천억에 매각한 인물의 "
                "사례가 언급되며, 목표 반복 입력의 신뢰 근거로 사용된다.\n"
            ),
        )

    if (
        "강사의 과거 상태" in issue_text or _missing_any(fixed, ["20대", "거절"])
    ) and _contains_any(source_text, ["20대", "거절"]):
        fixed = _insert_before_heading(
            fixed,
            "## 5.",
            (
                "\n### 강사의 과거 상태\n"
                "- 강사는 20대 중반 이전에는 자아가 약했고, 거절을 잘하지 못해 "
                "자기 일보다 타인의 일을 우선하던 시기가 있었다고 설명한다.\n"
            ),
        )

    if "스마트폰/SNS 사용 시간 사례" in issue_text and _contains_any(
        source_text, ["10시간", "폰 중독"]
    ):
        fixed = _insert_before_heading(
            fixed,
            "## 7.",
            (
                "\n### 스마트폰/SNS 사용 시간 사례\n"
                "- 강사는 과거 하루 10시간 이상 SNS와 스마트폰을 사용하던 상태를 "
                "예로 들며, 무의식 해킹이 필요한 이유를 설명한다.\n"
            ),
        )

    if (
        "매일 1% 성장" in issue_text or _missing_any(fixed, ["1%", "37배"])
    ) and _contains_any(source_text, ["1%", "37배"]):
        fixed = _insert_before_heading(
            fixed,
            "## 7.",
            (
                "\n### 매일 1% 성장\n"
                "- 강사는 매일 1%씩 성장하면 1년에 약 37배 성장한다는 말을 예로 "
                "들며, 매일 글쓰기와 작은 반복의 복리 효과를 설명한다.\n"
            ),
        )

    if (
        "최소 60일 이상 환경 유지" in issue_text
        or "60개 이상 채널 구독 사례" in issue_text
        or _missing_any(fixed, ["새 채널", "20~30", "60개", "60일", "66일"])
    ) and _contains_any(source_text, ["60일", "66일", "60개", "20", "30"]):
        fixed = _insert_before_heading(
            fixed,
            "## 8.",
            (
                "\n### 환경 유지 기준\n"
                "- 강사는 새 채널을 만들고 관심 주제 채널을 20~30개 구독하며, "
                "필요하면 60개 이상에서 100개까지 구독하라고 설명한다. 습관 형성에 "
                "약 66일이 걸린다는 점을 근거로 최소 60일 이상 같은 환경을 유지한다.\n"
            ),
        )

    if "멘토 내용을 그대로 따라야 하는 이유" in issue_text and _contains_any(
        source_text, ["그대로 따라", "성공방정식"]
    ):
        fixed = _insert_before_heading(
            fixed,
            "## 8.",
            (
                "\n### 멘토 내용을 그대로 따라야 하는 이유\n"
                "- 멘토가 알려주는 길은 이미 결과를 만든 성공방정식이므로, 초반에는 "
                "내용을 그대로 따라 실행해야 방향이 크게 틀어지지 않는다.\n"
            ),
        )

    if "내 생각 추가 금지" in issue_text and _contains_any(source_text, ["내 생각"]):
        fixed = _insert_before_heading(
            fixed,
            "## 9.",
            (
                "\n### 내 생각 추가 금지\n"
                "- 초반 실행에서는 내 생각 추가 금지가 중요하다. 먼저 검증된 방식을 "
                "그대로 실행한 뒤, 결과를 만든 다음 자기 방식으로 발전시킨다.\n"
            ),
        )

    if "미션 GPS 비유" in issue_text and _contains_any(source_text, ["GPS"]):
        fixed = _insert_before_heading(
            fixed,
            "## 9.",
            (
                "\n### 미션 GPS 비유\n"
                "- 강사는 미션에서 작성하는 플랜이 5월 100만원으로 이끌 GPS 같은 "
                "역할을 한다고 설명한다.\n"
            ),
        )

    if (
        "다음 단계 예고" in issue_text or _missing_any(fixed, ["1000만원", "1억원"])
    ) and _contains_any(source_text, ["1000만원", "1억원"]):
        fixed = _insert_before_heading(
            fixed,
            "## 13.",
            (
                "\n### 다음 강의 예고\n"
                "- 다음 단계에서는 5월 1000만원, 1월 1억원으로 이어지는 뇌 자동화 "
                "세팅법 심화 내용을 다룬다고 예고한다.\n"
            ),
        )

    return fixed


def _missing_any(text: str, terms: list[str]) -> bool:
    return any(term not in text for term in terms)


def _insert_before_heading(markdown: str, heading: str, insertion: str) -> str:
    index = markdown.find(heading)
    if index == -1:
        return markdown.rstrip() + "\n" + insertion.rstrip() + "\n"
    return markdown[:index].rstrip() + "\n" + insertion.rstrip() + "\n\n" + markdown[index:]


def _required_markdown_skeleton() -> str:
    return (
        "# {강의 제목}\n\n"
        "## 0. 한 줄 핵심\n\n"
        "## 1. 강의 목표\n\n"
        "## 2. 강의 전체 흐름\n\n"
        "## 3. 핵심 개념\n\n"
        "## 4. 강의 내용 상세 재구성\n\n"
        "## 5. 비교 / 구조화 정리\n\n"
        "## 6. 숫자 / 사례 정리\n\n"
        "## 7. 실전 적용 방법\n\n"
        "## 8. 강의 미션\n\n"
        "## 9. Obsidian 연결\n\n"
        "## 10. 내 프로젝트 적용\n\n"
        "## 11. 최종 핵심 정리\n\n"
        "## 12. 다음 액션"
    )


def _preservation_retry_excerpts(missing_labels: list[str], source_text: str) -> str:
    sections: list[str] = []
    for label, source_terms, _output_terms in PRESERVATION_CHECKS:
        if label not in missing_labels:
            continue
        excerpts = _source_excerpts(source_text, source_terms, limit=1)
        if not excerpts:
            continue
        sections.append(f"### {label}\n" + "\n".join(f"- {excerpt}" for excerpt in excerpts))
    return "\n\n".join(sections) if sections else "- 원문 전체를 다시 확인하세요."


def _contains_any(text: str, terms: list[str]) -> bool:
    normalized = text.lower()
    return any(term.lower() in normalized for term in terms)


def _source_excerpts(source_text: str, terms: list[str], limit: int = 2) -> list[str]:
    text = re.sub(r"\s+", " ", source_text).strip()
    if not text:
        return []

    excerpts: list[str] = []
    seen: set[str] = set()
    for term in terms:
        search_from = 0
        normalized_text = text.lower()
        normalized_term = term.lower()
        while len(excerpts) < limit:
            index = normalized_text.find(normalized_term, search_from)
            if index == -1:
                break
            excerpt = _excerpt_around_index(text, index)
            search_from = index + len(term)
            if excerpt and excerpt not in seen:
                excerpts.append(excerpt)
                seen.add(excerpt)
    return excerpts


def _excerpt_around_index(text: str, index: int, before: int = 180, after: int = 520) -> str:
    start = _previous_korean_boundary(text, max(0, index - before), index)
    end = _next_korean_boundary(text, index + after)
    excerpt = text[start:end].strip()
    if not excerpt:
        return ""
    return excerpt


def _previous_korean_boundary(text: str, fallback: int, index: int) -> int:
    window = text[fallback:index]
    boundaries = [match.end() for match in re.finditer(r"[.!?。！？]\s+", window)]
    if boundaries:
        return fallback + boundaries[-1]
    return fallback


def _next_korean_boundary(text: str, index: int) -> int:
    index = min(index, len(text))
    window = text[index : min(len(text), index + 260)]
    match = re.search(
        r"(습니다|합니다|됩니다|됩니다|겁니다|답니다|거랍니다|했습니다|되겠습니다|하세요|"
        r"인가요\?|까요\?|겠죠|이죠|이죠\?|죠\?|요\?|다\.|요\.|죠\.|까\?)",
        window,
    )
    if match:
        return index + match.end()
    punctuation = re.search(r"[.!?。！？]", window)
    if punctuation:
        return index + punctuation.end()
    return index
