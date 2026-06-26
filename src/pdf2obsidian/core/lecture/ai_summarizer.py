from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from pdf2obsidian.core.ai.ollama_client import reconstruct_with_ollama
from pdf2obsidian.core.lecture.prompt_loader import load_prompt
from pdf2obsidian.core.transcript_processor import TranscriptBlock

ProgressCallback = Callable[[int, str], None]


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
    progress: ProgressCallback | None = None,
) -> AIReconstructionResult:
    last_progress = -1

    def emit_progress(percent: int, message: str) -> None:
        nonlocal last_progress
        bounded = max(last_progress, min(100, max(0, percent)))
        if progress and bounded > last_progress:
            progress(bounded, message)
            last_progress = bounded

    source_text = "\n\n".join(block.text for block in blocks if block.text.strip())
    if not source_text.strip():
        return AIReconstructionResult(
            markdown="",
            chunks=0,
            warning="No transcript text was found.",
        )

    emit_progress(5, "Preparing Ollama transcript reconstruction.")
    resolved_language = _resolve_output_language(output_language, source_text)
    template = _build_language_prompt(load_prompt("lecture_study_note_ko"), resolved_language)
    chunks = chunk_text(source_text, max_chars=max_chars)
    chunk_template = (
        _chunk_reconstruction_prompt(template, resolved_language)
        if len(chunks) > 1
        else template
    )
    reconstructions: list[str] = []
    total_chunks = max(len(chunks), 1)
    for chunk_index, chunk in enumerate(chunks, start=1):
        if total_chunks == 1:
            start_message = "Ollama one-shot reconstruction started."
            finish_message = "Ollama one-shot reconstruction finished."
        else:
            start_message = f"Ollama chunk {chunk_index}/{total_chunks} started."
            finish_message = f"Ollama chunk {chunk_index}/{total_chunks} finished."
        emit_progress(
            10 + int(((chunk_index - 1) / total_chunks) * 45),
            start_message,
        )
        reconstructions.append(
            reconstruct_with_ollama(
                chunk,
                model=model,
                template=chunk_template,
                base_url=base_url,
            )
        )
        emit_progress(
            10 + int((chunk_index / total_chunks) * 45),
            finish_message,
        )

    failed = [
        reconstruction
        for reconstruction in reconstructions
        if reconstruction.startswith("Ollama reconstruction failed:")
    ]
    if failed:
        return AIReconstructionResult(markdown="", chunks=len(chunks), warning=failed[0])

    combined = "\n\n".join(reconstructions)
    if len(reconstructions) > 1:
        emit_progress(60, "Merging Ollama chunk notes.")
        final_prompt = _merge_reconstruction_prompt(template, resolved_language, source_text)
        combined = reconstruct_with_ollama(
            combined,
            model=model,
            template=final_prompt,
            base_url=base_url,
        )
        if combined.startswith("Ollama reconstruction failed:"):
            return AIReconstructionResult(markdown="", chunks=len(chunks), warning=combined)
        emit_progress(70, "Ollama chunk merge finished.")

    emit_progress(82, "Post-processing Ollama reconstruction.")
    markdown = _normalize_final_markdown(
        combined,
        title=title,
        source_type=source_type,
        source_file=source_file,
        resolved_language=resolved_language,
    )

    quality_issues = _final_quality_issues(markdown, source_text, resolved_language)
    if quality_issues:
        emit_progress(
            90,
            "Ollama output saved without retry; quality issues may remain.",
        )

    markdown = _remove_lone_hash_lines(markdown)
    emit_progress(100, "Ollama reconstruction finished.")
    return AIReconstructionResult(markdown=markdown, chunks=len(chunks))


def _normalize_final_markdown(
    markdown: str,
    title: str,
    source_type: str,
    source_file: str,
    resolved_language: str = "auto",
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

    content = _remove_thinking_traces(content)
    content = _replace_wiki_links_with_plain_text(content)
    content = _remove_dangling_wiki_link_brackets(content)
    content = _sanitize_final_headings(content, resolved_language)
    if resolved_language == "ko":
        content = _replace_korean_importance_hanja(content)
    content = _remove_lone_hash_lines(content)
    content_body = _content_without_frontmatter(content)
    content_body = _strip_prompt_leak_prefix(content_body, resolved_language)

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
    return "en"


def _build_language_prompt(template: str, output_language: str) -> str:
    language = output_language.lower().strip()
    if language == "ko":
        instruction = (
            "최우선 지시: 출력 언어는 한국어입니다.\n"
            "입력 원문이 한국어이면 최종 Markdown 전체를 반드시 자연스러운 한국어로 작성합니다.\n"
            "영어 또는 중국어로 섹션 본문을 쓰지 않습니다.\n"
            "표의 중요도도 '매우 높음/높음/중간/낮음'처럼 한국어로 씁니다.\n"
            "고유명사, 제품명, 도구명, 명령어, 코드, 파일명은 필요한 경우 "
            "원문 표기를 유지합니다.\n\n"
            "작업 목표: 짧은 요약이 아니라 강의를 대체할 수 있는 Markdown 학습자료를 만듭니다.\n"
            "강의를 보지 않은 사람이 이 문서만 읽어도 강의보다 더 쉽게 "
            "이해하고 실행할 수 있어야 합니다.\n"
            "원문에 있는 개념, 이유, 예시, 숫자, 실행 절차, 미션을 "
            "본문 구조 안에 충분히 풀어서 씁니다.\n"
            "원문에 있는 구체적인 용어, 수치, 사례, 과제는 별도 보강 섹션으로 붙이지 말고 "
            "관련 본문 섹션에 자연스럽게 통합합니다.\n"
            "최종 Markdown은 0번부터 12번 섹션까지만 사용하고, "
            "13번 또는 추가 정보 섹션을 만들지 않습니다.\n"
            "최종 Markdown 제목과 섹션 제목은 한국어 제목만 사용합니다.\n"
            "`Lecture Overview / 강의 전체 요약` 같은 병기 제목을 출력하지 않습니다.\n"
            "Thinking, Reasoning, Analysis, 내부 추론 과정은 출력하지 않습니다.\n"
        )
    elif language == "en":
        instruction = (
            "Output language: English. Translate and rewrite the lecture into clear English. "
            "Keep proper nouns, tool names, commands, and code in their original form when needed. "
            "Use English-only final Markdown headings. Do not output bilingual headings. "
            "Do not output thinking, reasoning, analysis, or hidden scratchpad text."
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
            "Do not compress this chunk into broad lessons. Treat this chunk as evidence "
            "inventory for the final note: keep distinct concepts, examples, numeric "
            "details, procedures, warnings, and assignments separate."
        )
    return (
        f"{template}\n\n"
        "청크 단계 지시:\n"
        "지금 입력은 전체 강의의 일부입니다. 최종본을 완성하려고 하지 말고, "
        "이 구간에 들어 있는 정보 재료를 최대한 보존한 상세 재구성 노트를 작성하세요.\n"
        "이 청크는 최종 병합을 위한 근거 inventory입니다.\n"
        "숫자, 사례, 강사의 경험, 비유, 실행 절차, 미션 단서, 주의사항을 빠뜨리지 마세요.\n"
        "서로 다른 개념, 예시, 절차, 주의사항은 각각 구분해서 남기세요.\n"
        "숫자와 구체 정보는 숫자/사례 후보 목록처럼 따로 보존하세요.\n"
        "원문에 절차가 있으면 번호 목록으로 복원하세요.\n"
        "원문을 그대로 붙이지 말고 자연스러운 한국어 문장으로 정리하세요.\n"
        "다만 짧게 요약하지 말고, 나중에 병합할 수 있도록 구체적인 내용을 충분히 남기세요.\n"
        "이 단계에서는 일반론이나 추상 표현만 반복하지 마세요.\n"
        "가능하면 최종 Markdown 구조를 유지하되, 이 청크에 없는 내용은 억지로 채우지 마세요.\n"
    )


def _merge_reconstruction_prompt(
    template: str,
    resolved_language: str,
    source_text: str,
) -> str:
    coverage_brief = _source_coverage_brief(source_text)
    quality_targets = _quality_target_brief(source_text)
    if resolved_language != "ko":
        return (
            f"{template}\n\n"
            "Merge stage: combine the chunk notes into one final Obsidian Markdown study "
            "note. Preserve details from every chunk. Do not summarize away examples, "
            "numbers, missions, or action steps. Use enough flow rows, concept "
            "subsections, detailed reconstruction subsections, and number/example rows "
            "for the source.\n\n"
            f"Quality targets:\n{quality_targets}\n\n"
            f"Coverage priorities:\n{coverage_brief}"
        )
    return (
        f"{template}\n\n"
        "병합 단계 지시:\n"
        "입력은 원본 자막을 여러 구간으로 나눠 재구성한 청크 노트입니다.\n"
        "청크 노트를 단순히 이어붙이지 말고, 하나의 완성된 Obsidian 강의 재구성 MD로 "
        "다시 작성하세요.\n"
        "목표 스타일은 책의 한 챕터처럼 읽히는 학습자료입니다.\n"
        "각 청크에 있는 구체적인 숫자, 사례, 비유, 실행 단계, 미션을 최종본에 보존하세요.\n"
        "특히 숫자/사례 표에는 원문에 등장한 숫자를 가능한 한 모두 정리하세요.\n"
        "강의 흐름 표는 실제 강의 전환점마다 행을 만들고, "
        "핵심 개념과 상세 재구성은 원문 개념 단위로 소제목을 충분히 나누세요.\n"
        "실행 절차는 번호 목록으로 복원하고, 미션/과제가 있으면 목적과 수행 방법을 분리하세요.\n"
        "반복은 제거하되 세부 정보는 삭제하지 마세요.\n"
        "일반 문장 반복으로 분량을 채우지 마세요.\n"
        "청크에 덜 다듬어진 자막 문장이 있더라도 원문 덩어리로 붙이지 말고 "
        "자연스러운 설명 문장으로 재작성하세요.\n"
        "출력은 반드시 `# 강의 제목`, `## 0. 한 문장 핵심`부터 시작되는 완성본이어야 합니다.\n"
        "중간 섹션만 출력하거나 0~3번 섹션을 생략하면 실패입니다.\n"
        "최종 Markdown은 반드시 0번부터 12번 섹션까지만 사용하세요.\n"
        "아래 보존 우선순위를 최종본의 관련 섹션에 자연스럽게 녹이세요.\n\n"
        f"품질 목표:\n{quality_targets}\n\n"
        f"보존 우선순위:\n{coverage_brief}\n"
    )


def _language_retry_prompt(template: str, resolved_language: str) -> str:
    if resolved_language == "ko":
        return (
            f"{template}\n\n"
            "중요: 이전 출력의 언어가 잘못되었습니다. 이번 출력은 반드시 한국어로만 작성하세요. "
            "최종 Markdown 제목과 섹션 제목도 한국어만 사용하세요. "
            "`Lecture Overview / 강의 전체 요약` 같은 영어/한국어 병기 제목을 쓰지 마세요. "
            "영어 문장이나 중국어 중요도 표기(高, 中, 低)를 사용하지 마세요. "
            "중요도는 '매우 높음', '높음', '중간', '낮음'처럼 한국어로 쓰세요. "
            "Thinking, Reasoning, Analysis, 내부 추론 과정은 출력하지 마세요."
        )
    return template


def _reconstruct_generic_partial_sections(
    source_text: str,
    model: str,
    base_template: str,
    resolved_language: str,
    base_url: str,
    progress: ProgressCallback | None = None,
) -> str:
    prompts = _generic_partial_section_prompts(base_template, resolved_language, source_text)
    sections: list[str] = []
    total_prompts = max(len(prompts), 1)
    for prompt_index, (prompt, start_marker, stop_markers) in enumerate(prompts, start=1):
        if progress:
            progress(
                92 + int(((prompt_index - 1) / total_prompts) * 6),
                f"Ollama generic section reconstruction {prompt_index}/{total_prompts} started.",
            )
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
        if progress:
            progress(
                92 + int((prompt_index / total_prompts) * 6),
                f"Ollama generic section reconstruction {prompt_index}/{total_prompts} finished.",
            )

    return "\n\n".join(part.strip() for part in sections if part.strip())


def _generic_partial_section_prompts(
    base_template: str,
    resolved_language: str,
    source_text: str,
) -> list[tuple[str, str, list[str]]]:
    _ = base_template
    quality_targets = _quality_target_brief(source_text)
    coverage_brief = _source_coverage_brief(source_text)
    count_targets = _section_count_target_brief(source_text)
    if resolved_language != "ko":
        common = (
            "Generic section reconstruction fallback:\n"
            "You are writing only the requested section range from the full source. "
            "Do not write sections outside the requested range. Do not summarize thinly. "
            "Preserve source-grounded concepts, examples, numeric details, procedures, "
            "missions, cautions, and next actions. Use plain text related-note candidates, "
            "not Obsidian wiki links. Use English-only headings and do not output "
            "thinking, reasoning, or analysis traces.\n\n"
            f"Quality targets:\n{quality_targets}\n\n"
            f"Minimum section targets:\n{count_targets}\n\n"
            f"Coverage priorities:\n{coverage_brief}\n\n"
        )
        return [
            (
                common
                + "Write exactly this range only: `# {Lecture Title}`, `## 0. One "
                "Sentence Core`, `## 1. Lecture Overview`, and `## 2. Lecture Flow`. "
                "The flow table should have enough rows for the real lecture turns.",
                "# ",
                ["## 3."],
            ),
            (
                common
                + "Write exactly section `## 3. Key Concepts` only. Create separate "
                "3-x subsections for distinct concepts, methods, examples, warnings, "
                "stories, and procedures.",
                "## 3.",
                ["## 4."],
            ),
            (
                common
                + "Write exactly section `## 4. Detailed Lecture Reconstruction` only. "
                "This must be the main study-chapter body, with enough 4-x subsections "
                "to preserve the source logic, examples, procedures, and explanations.",
                "## 4.",
                ["## 5."],
            ),
            (
                common
                + "Write exactly sections `## 5. Comparison and Structured Summary` and "
                "`## 6. Numbers and Examples`. The Numbers and Examples table must use "
                "one row per meaningful numeric or concrete detail.",
                "## 5.",
                ["## 7."],
            ),
            (
                common
                + "Write exactly sections `## 7. Practical Actions` and `## 8. Mission`. "
                "Restore procedures as numbered steps and missions as purpose plus method.",
                "## 7.",
                ["## 9."],
            ),
            (
                common
                + "Write exactly sections `## 9. Obsidian Connections` and `## 10. "
                "Personal or Project Application`. Related-note candidates must be plain "
                "Markdown bullet text, never `[[wiki links]]`.",
                "## 9.",
                ["## 11."],
            ),
            (
                common
                + "Write exactly sections `## 11. Final Takeaways` and `## 12. Next "
                "Actions`. Next actions must be practical Markdown task list items. "
                "Do not create any section after `## 12. Next Actions`.",
                "## 11.",
                ["## 13."],
            ),
        ]

    common = (
        "범용 섹션별 재구성 fallback:\n"
        "지금은 전체 원문에서 지정된 섹션 범위만 작성합니다.\n"
        "요청 범위 밖의 섹션은 작성하지 마세요.\n"
        "짧은 요약으로 줄이지 말고, 원문에 근거한 개념, 예시, 숫자, 절차, "
        "미션, 주의사항, 다음 액션을 보존하세요.\n"
        "관련 노트 후보에는 Obsidian 위키링크를 쓰지 말고 일반 텍스트 불릿만 사용하세요.\n\n"
        "최종 제목은 한국어 제목만 사용하고 영어/한국어 병기 제목을 쓰지 마세요.\n"
        "Thinking, Reasoning, Analysis, 내부 추론 과정은 출력하지 마세요.\n\n"
        f"품질 목표:\n{quality_targets}\n\n"
        f"최소 섹션 목표:\n{count_targets}\n\n"
        f"보존 우선순위:\n{coverage_brief}\n\n"
    )
    return [
        (
            common
            + "정확히 이 범위만 작성하세요: `# {강의 제목}`, `## 0. 한 문장 핵심`, "
            "`## 1. 강의 전체 요약`, `## 2. 강의 흐름 구조`.\n"
            "강의 흐름 표는 실제 강의 전환점마다 충분한 행을 만들어야 합니다.",
            "# ",
            ["## 3."],
        ),
        (
            common
            + "`## 3. 핵심 개념 정리` 섹션만 작성하세요.\n"
            "서로 다른 개념, 방법, 예시, 주의사항, 이야기, 절차마다 3-x 소제목을 "
            "충분히 만드세요.",
            "## 3.",
            ["## 4."],
        ),
        (
            common
            + "`## 4. 강의 내용 상세 정리` 섹션만 작성하세요.\n"
            "이 섹션은 짧은 요약이 아니라 학습 챕터의 본문이어야 합니다.\n"
            "원문 논리, 예시, 절차, 설명을 보존하기 위해 4-x 소제목을 충분히 만드세요.",
            "## 4.",
            ["## 5."],
        ),
        (
            common
            + "`## 5. 비교와 구조화 정리`와 `## 6. 숫자와 사례 정리`만 작성하세요.\n"
            "숫자와 사례 표는 의미 있는 숫자 또는 구체 정보마다 한 행을 사용하세요.\n"
            "주제명만 반복하지 말고 원문에 나온 실제 숫자, 기간, 개수, 사례를 쓰세요.",
            "## 5.",
            ["## 7."],
        ),
        (
            common
            + "`## 7. 실전 적용 방법`과 `## 8. 강의 미션 정리`만 작성하세요.\n"
            "절차는 번호 목록으로, 미션은 목적과 수행 방법으로 복원하세요.",
            "## 7.",
            ["## 9."],
        ),
        (
            common
            + "`## 9. Obsidian 연결`과 `## 10. 개인 또는 프로젝트 적용`만 작성하세요.\n"
            "관련 노트 후보는 일반 Markdown 불릿 텍스트로만 작성하고 "
            "`[[위키링크]]`를 절대 만들지 마세요.",
            "## 9.",
            ["## 11."],
        ),
        (
            common
            + "`## 11. 최종 핵심 정리`와 `## 12. 다음 액션`만 작성하세요.\n"
            "다음 액션은 실제로 실행 가능한 Markdown 체크리스트로 작성하세요.",
            "## 11.",
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


def _replace_wiki_links_with_plain_text(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        target = match.group(1).strip()
        if "|" in target:
            return target.split("|", 1)[1].strip()
        return target

    return re.sub(r"\[\[([^\[\]]+)\]\]", replace, text)


def _remove_dangling_wiki_link_brackets(text: str) -> str:
    return text.replace("[[", "").replace("]]", "")


_EN_TO_KO_HEADINGS = {
    "One Sentence Core": "한 문장 핵심",
    "Lecture Overview": "강의 전체 요약",
    "Lecture Flow": "강의 흐름 구조",
    "Key Concepts": "핵심 개념 정리",
    "Detailed Lecture Reconstruction": "강의 내용 상세 정리",
    "Comparison / Structured Summary": "비교와 구조화 정리",
    "Comparison and Structured Summary": "비교와 구조화 정리",
    "Numbers / Examples": "숫자와 사례 정리",
    "Numbers and Examples": "숫자와 사례 정리",
    "Practical Actions": "실전 적용 방법",
    "Mission": "강의 미션 정리",
    "Obsidian Connections": "Obsidian 연결",
    "Personal / Project Application": "개인 또는 프로젝트 적용",
    "Personal or Project Application": "개인 또는 프로젝트 적용",
    "Final Takeaways": "최종 핵심 정리",
    "Next Actions": "다음 액션",
}

_KO_TO_EN_HEADINGS = {value: key for key, value in _EN_TO_KO_HEADINGS.items()}
_KO_TO_EN_HEADINGS.update(
    {
        "비교와 구조화 정리": "Comparison and Structured Summary",
        "숫자와 사례 정리": "Numbers and Examples",
        "개인 또는 프로젝트 적용": "Personal or Project Application",
    }
)


def _sanitize_final_headings(text: str, resolved_language: str) -> str:
    language = resolved_language.lower().strip()
    if language not in {"ko", "en"}:
        return text

    sanitized_lines: list[str] = []
    for line in text.splitlines():
        heading_match = re.match(r"^(#{1,6}\s+)(.+)$", line)
        if not heading_match:
            sanitized_lines.append(line)
            continue
        prefix, heading = heading_match.groups()
        heading = _sanitize_bilingual_heading_text(heading, language)
        heading = _replace_known_heading_language(heading, language)
        sanitized_lines.append(f"{prefix}{heading}".rstrip())
    return "\n".join(sanitized_lines)


def _replace_korean_importance_hanja(text: str) -> str:
    replacements = {
        "非常高": "매우 높음",
        "高": "높음",
        "中": "중간",
        "低": "낮음",
    }
    result = text
    for source, target in replacements.items():
        result = re.sub(rf"(?<![가-힣A-Za-z]){re.escape(source)}(?![가-힣A-Za-z])", target, result)
    return result


def _strip_prompt_leak_prefix(text: str, resolved_language: str) -> str:
    stripped_text = text.strip()
    if not stripped_text:
        return ""

    lines = stripped_text.splitlines()
    section_zero_indexes = [
        index
        for index, line in enumerate(lines)
        if re.match(r"^##\s*0[.)]?\s+", line.strip())
    ]
    for section_index in section_zero_indexes:
        title_index = _nearest_non_prompt_h1_before(lines, section_index)
        if title_index is not None:
            return "\n".join(lines[title_index:]).strip()

    if section_zero_indexes:
        return "\n".join(lines[section_zero_indexes[0] :]).strip()

    if _contains_prompt_leak_heading(stripped_text):
        first_non_prompt_h1 = _first_non_prompt_h1(lines)
        if first_non_prompt_h1 is not None:
            return "\n".join(lines[first_non_prompt_h1:]).strip()

    return stripped_text


def _nearest_non_prompt_h1_before(lines: list[str], before_index: int) -> int | None:
    for index in range(before_index - 1, -1, -1):
        heading = lines[index].strip()
        if not re.match(r"^#\s+[^#]", heading):
            continue
        if not _is_prompt_leak_heading(heading):
            return index
    return None


def _first_non_prompt_h1(lines: list[str]) -> int | None:
    for index, line in enumerate(lines):
        heading = line.strip()
        if re.match(r"^#\s+[^#]", heading) and not _is_prompt_leak_heading(heading):
            return index
    return None


def _is_prompt_leak_heading(heading: str) -> bool:
    normalized = re.sub(r"^#+\s*", "", heading).strip().lower()
    normalized = re.sub(r"^\d+[.)]?\s*", "", normalized)
    prompt_markers = (
        "primary goal",
        "최우선 목표",
        "output language",
        "출력 언어",
        "absolute rules",
        "절대 원칙",
        "information preservation",
        "정보 보존 원칙",
        "quality targets",
        "품질 목표",
        "transcript processing",
        "자막 처리 규칙",
        "writing style",
        "문체 규칙",
        "fixed markdown structure",
        "고정 markdown 출력 구조",
        "korean final structure",
        "한국어 최종 구조",
        "english final structure",
        "영어 최종 구조",
        "obsidian rules",
        "validation",
        "final output requirements",
        "최종 출력",
        "검증",
    )
    return any(marker in normalized for marker in prompt_markers)


def _contains_prompt_leak_heading(text: str) -> bool:
    return any(
        _is_prompt_leak_heading(line.strip())
        for line in text.splitlines()
        if line.lstrip().startswith("#")
    )


def _sanitize_bilingual_heading_text(heading: str, language: str) -> str:
    if "/" not in heading:
        return heading
    if not re.search(r"[A-Za-z]", heading) or not re.search(r"[가-힣]", heading):
        return heading

    left, right = [part.strip() for part in heading.split("/", 1)]
    if language == "en":
        return left

    number_prefix = ""
    number_match = re.match(r"^(\d+(?:[-.]\d+)?\.?\s+)", left)
    if number_match:
        number_prefix = number_match.group(1)
    if number_prefix and not right.startswith(number_prefix.strip()):
        return f"{number_prefix}{right}"
    return right


def _replace_known_heading_language(heading: str, language: str) -> str:
    mapping = _EN_TO_KO_HEADINGS if language == "ko" else _KO_TO_EN_HEADINGS
    replaced = heading
    for source, target in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True):
        flags = re.IGNORECASE if language == "ko" else 0
        replaced = re.sub(re.escape(source), target, replaced, flags=flags)
    return replaced


def _remove_thinking_traces(text: str) -> str:
    without_blocks = re.sub(
        r"(?is)<think\b[^>]*>.*?</think>",
        "",
        text,
    )
    filtered_lines: list[str] = []
    for line in without_blocks.splitlines():
        if _is_thinking_trace_line(line):
            continue
        filtered_lines.append(line)
    return "\n".join(filtered_lines).strip()


def _is_thinking_trace_line(line: str) -> bool:
    stripped = line.strip()
    normalized = stripped.lower().strip("#:>-*` ")
    if not normalized:
        return False
    forbidden_exact = {
        "thinking",
        "thinking...",
        "...done thinking.",
        "reasoning",
        "analysis",
        "internal reasoning",
        "internal analysis",
        "internal planning",
        "scratchpad",
        "사고 과정",
        "추론 과정",
        "분석 과정",
        "내부 계획",
        "숨은 메모",
    }
    if normalized in forbidden_exact:
        return True
    forbidden_prefixes = (
        "thinking",
        "thinking:",
        "reasoning",
        "reasoning:",
        "analysis",
        "analysis:",
        "here's a thinking process",
        "here is a thinking process",
        "internal planning",
        "internal reasoning:",
        "internal analysis:",
        "사고 과정",
        "추론 과정",
        "분석 과정",
        "내부 계획",
    )
    return any(normalized.startswith(prefix) for prefix in forbidden_prefixes)


def _contains_thinking_trace(text: str) -> bool:
    if re.search(r"(?is)<think\b[^>]*>.*?</think>", text):
        return True
    return any(_is_thinking_trace_line(line) for line in text.splitlines())


def _final_quality_issues(
    markdown: str,
    source_text: str,
    resolved_language: str = "auto",
) -> list[str]:
    return _structure_quality_issues(
        markdown,
        source_text,
        resolved_language,
    ) + _coverage_quality_issues(markdown, source_text)


def _structure_quality_issues(
    markdown: str,
    source_text: str,
    resolved_language: str = "auto",
) -> list[str]:
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

    if (
        "CURRENT MARKDOWN TO REVISE" in markdown
        or "MISSING SOURCE EXCERPTS" in markdown
        or _contains_prompt_leak_heading(body)
    ):
        issues.append("prompt text leaked into output")

    if "[[" in markdown or "]]" in markdown:
        issues.append("Obsidian wiki links are not allowed in generated lecture notes")

    if _contains_thinking_trace(markdown):
        issues.append("thinking, reasoning, or analysis traces are not allowed")

    issues.extend(_heading_language_issues(body, resolved_language))

    return issues


def _heading_language_issues(markdown_body: str, resolved_language: str) -> list[str]:
    issues: list[str] = []
    heading_lines = [
        line.strip()
        for line in markdown_body.splitlines()
        if line.lstrip().startswith("#")
    ]
    bilingual_heading_pattern = re.compile(
        r"^#{1,6}\s+.*(?:[A-Za-z][^#\n]*/[^#\n]*[가-힣]|[가-힣][^#\n]*/[^#\n]*[A-Za-z])"
    )
    if any(bilingual_heading_pattern.search(line) for line in heading_lines):
        issues.append("bilingual final headings are not allowed")

    language = resolved_language.lower().strip()
    if language == "ko":
        english_section_titles = (
            "One Sentence Core",
            "Lecture Overview",
            "Lecture Flow",
            "Key Concepts",
            "Detailed Lecture Reconstruction",
            "Comparison / Structured Summary",
            "Numbers / Examples",
            "Practical Actions",
            "Mission",
            "Obsidian Connections",
            "Personal / Project Application",
            "Final Takeaways",
            "Next Actions",
        )
        if any(
            title.lower() in line.lower()
            for line in heading_lines
            for title in english_section_titles
        ):
            issues.append("Korean output must use Korean-only final section headings")
    elif language == "en":
        korean_section_titles = (
            "한 문장 핵심",
            "강의 전체 요약",
            "강의 흐름 구조",
            "핵심 개념 정리",
            "강의 내용 상세 정리",
            "비교와 구조화 정리",
            "숫자와 사례 정리",
            "실전 적용 방법",
            "강의 미션 정리",
            "Obsidian 연결",
            "개인 또는 프로젝트 적용",
            "최종 핵심 정리",
            "다음 액션",
        )
        if any(title in line for line in heading_lines for title in korean_section_titles):
            issues.append("English output must use English-only final section headings")
    return issues


def _coverage_quality_issues(markdown: str, source_text: str) -> list[str]:
    if len(source_text) < 1000:
        return []

    issues: list[str] = []
    body = _content_without_frontmatter(markdown)
    min_expected_chars = _minimum_expected_body_chars(source_text)
    if len(body) < min_expected_chars:
        issues.append(
            "generated Markdown is too short for the source transcript "
            f"({len(body)} chars, expected at least {min_expected_chars})"
        )

    numeric_issues = _numeric_detail_quality_issues(markdown, source_text)
    if numeric_issues:
        issues.extend(numeric_issues)

    if len(source_text) >= 6000 and _concept_detail_subsection_count(body) < 8:
        issues.append(
            "not enough concept/detail subsections for a long transcript "
            "(create more source-grounded 3-x and 4-x subsections)"
        )

    return issues


def _minimum_expected_body_chars(source_text: str) -> int:
    if len(source_text) < 1000:
        return 0
    if len(source_text) < 3000:
        return max(900, int(len(source_text) * 0.45))
    if len(source_text) < 8000:
        return max(1800, int(len(source_text) * 0.60))
    return min(14000, max(6000, int(len(source_text) * 0.75)))


def _numeric_detail_quality_issues(markdown: str, source_text: str) -> list[str]:
    source_tokens = _numeric_detail_tokens(source_text)
    if len(source_tokens) < 6:
        return []

    normalized_markdown = _normalize_numeric_detail_text(markdown)
    matched = [
        token
        for token in source_tokens
        if _normalize_numeric_detail_text(token) in normalized_markdown
    ]
    required = max(4, int(len(source_tokens) * 0.55))
    if len(matched) >= required:
        return []

    return [
        "too many source numbers or concrete details are missing "
        f"({len(matched)}/{len(source_tokens)} preserved, expected at least {required})"
    ]


def _numeric_detail_tokens(text: str) -> list[str]:
    normalized = text.replace(",", "")
    pattern = re.compile(
        r"\d+(?:\.\d+)?\s*(?:[~\-]\s*\d+(?:\.\d+)?)?\s*"
        r"(?:%|퍼센트|원|만원|억원|개|명|년|개월|달|주|일|시간|분|초|번|배|단계|도|월)?"
    )
    tokens: list[str] = []
    seen: set[str] = set()
    for match in pattern.finditer(normalized):
        token = match.group(0).strip()
        if not token:
            continue
        normalized_token = _normalize_numeric_detail_text(token)
        if normalized_token in seen:
            continue
        seen.add(normalized_token)
        tokens.append(token)
    return tokens


def _normalize_numeric_detail_text(text: str) -> str:
    return re.sub(r"\s+", "", text.replace(",", "")).lower()


def _concept_detail_subsection_count(markdown: str) -> int:
    return len(re.findall(r"(?m)^###\s+(?:3|4)(?:[-.]\d+|\s*[-:])", markdown))


def _quality_retry_prompt(
    template: str,
    quality_issues: list[str],
    source_text: str,
    resolved_language: str,
) -> str:
    issue_list = "\n".join(f"- {issue}" for issue in quality_issues)
    coverage_brief = _source_coverage_brief(source_text)
    quality_targets = _quality_target_brief(source_text)
    if resolved_language == "en":
        return (
            f"{template}\n\n"
            "Important: the previous output did not satisfy the v1.1 lecture "
            "reconstruction quality rules.\n"
            "Rewrite the complete Markdown document from the source transcript.\n"
            "Use English-only final Markdown headings. Do not output bilingual headings "
            "such as `Lecture Overview / 강의 전체 요약`.\n"
            "Do not include Obsidian wiki links such as `[[Note Name]]` anywhere.\n"
            "Do not output thinking, reasoning, analysis, hidden scratchpad, or internal "
            "planning text.\n"
            "Do not add section 13 or extra quality-check sections.\n"
            "If the previous output was too short, missed numeric details, or lacked "
            "subsections, treat it as a thin summary and reconstruct from the full source.\n"
            "The Detailed Lecture Reconstruction section must read like the main body of "
            "a study chapter, not a short summary.\n\n"
            "Issues to fix:\n"
            f"{issue_list}\n\n"
            "Quality targets:\n"
            f"{quality_targets}\n\n"
            "Coverage priorities:\n"
            f"{coverage_brief}\n\n"
            "Required final Markdown skeleton:\n"
            f"{_required_markdown_skeleton(resolved_language)}\n\n"
            "Source excerpts to review:\n"
            f"{_source_review_excerpts(source_text)}\n"
        )
    return (
        f"{template}\n\n"
        "중요: 이전 출력은 범용 강의 재구성 품질 기준을 충족하지 못했습니다.\n"
        "이번에는 현재 Markdown을 기반으로 전체 문서를 다시 완성하세요.\n"
        "아래 수정 항목을 반드시 해결하고, 원문에 있는 핵심 개념, 숫자, "
        "예시, 절차, 과제, 주의사항을 관련 본문 섹션에 자연스럽게 반영하세요.\n"
        "수정 항목에 최소 글자 수, 숫자 보존 부족, 소제목 부족이 있다면 "
        "이전 결과를 요약본으로 간주하고 원문 전체에서 새로 재구성하세요.\n"
        "예상 최소 글자 수가 제시된 경우 그보다 충분히 긴 결과를 작성하세요.\n"
        "서로 다른 개념과 절차를 두세 개의 넓은 카테고리로 뭉개지 말고, "
        "원문에 등장하는 구체적인 개념 단위로 소제목과 표 행을 충분히 늘리세요.\n"
        "긴 강의라면 3번 핵심 개념과 4번 상세 재구성에 여러 개의 3-x, 4-x 소제목을 만드세요.\n"
        "숫자/사례 섹션은 넓은 주제명이 아니라 원문에 나온 실제 숫자, 날짜, 금액, "
        "개수, 기간, 비율, 사례를 하나씩 정리해야 합니다.\n"
        "Obsidian 연결 섹션에서도 `[[노트명]]` 위키링크를 만들지 말고 "
        "일반 Markdown 불릿 텍스트만 사용하세요.\n"
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
        f"{issue_list}\n\n"
        "품질 목표:\n"
        f"{quality_targets}\n\n"
        "보존 우선순위:\n"
        f"{coverage_brief}\n\n"
        "반드시 사용할 최종 Markdown 골격:\n"
        f"{_required_markdown_skeleton(resolved_language)}\n\n"
        "원문 참고 발췌:\n"
        f"{_source_review_excerpts(source_text)}\n"
    )


def _quality_retry_input(
    markdown: str,
    source_text: str,
    quality_issues: list[str],
    discard_current: bool = False,
) -> str:
    issue_list = "\n".join(f"- {issue}" for issue in quality_issues)
    if discard_current:
        return "\n\n".join(
            [
                "이전 결과는 필수 항목이나 섹션을 크게 누락했으므로 참고하지 말고 폐기하세요.",
                "해결해야 할 품질 이슈:",
                issue_list,
                "본문에 통합해야 할 원문 참고:",
                _source_review_excerpts(source_text),
                "전체 원문 자막:",
                source_text.strip(),
            ]
        )
    return "\n\n".join(
        [
            "수정할 현재 Markdown:",
            markdown.strip(),
            "해결해야 할 품질 이슈:",
            issue_list,
            "본문에 통합해야 할 원문 참고:",
            _source_review_excerpts(source_text),
            "전체 원문 자막:",
            source_text.strip(),
        ]
    )


def _should_discard_current_markdown(quality_issues: list[str]) -> bool:
    discard_markers = [
        "필수 섹션 누락",
        "too short",
        "too many source numbers",
        "not enough concept/detail subsections",
        "bilingual final headings",
        "Korean output must use Korean-only",
        "English output must use English-only",
        "thinking, reasoning, or analysis traces",
        "Obsidian wiki links",
    ]
    return len(quality_issues) >= 8 or any(
        marker in issue for issue in quality_issues for marker in discard_markers
    )


def _source_coverage_brief(source_text: str) -> str:
    priorities = [
        "- full lecture flow and conclusion",
        "- key concepts and their explanations",
        "- concrete examples, analogies, and case details",
        "- numbers, dates, durations, quantities, and other measurable details",
        "- procedures, action steps, missions, assignments, cautions, and next actions",
    ]
    if not re.search(r"\d", source_text):
        priorities[3] = "- any concrete details, examples, names, or distinctions in the source"
    numeric_tokens = _numeric_detail_tokens(source_text)
    if numeric_tokens:
        marker_list = ", ".join(numeric_tokens[:40])
        suffix = " ..." if len(numeric_tokens) > 40 else ""
        priorities.append(f"- source numeric/detail markers to review: {marker_list}{suffix}")
    return "\n".join(priorities)


def _quality_target_brief(source_text: str) -> str:
    targets = [
        "- preserve lecture logic flow instead of only topic labels",
        "- create one flow-table row per meaningful lecture turn",
        "- create separate concept subsections for distinct concepts, methods, warnings, "
        "and examples",
        "- make Detailed Lecture Reconstruction the main explanatory body",
        "- use one Numbers / Examples row per meaningful numeric or concrete detail",
        "- restore procedures as numbered steps and missions as purpose plus method",
        "- use plain text related-note candidates, not Obsidian wiki links",
    ]
    minimum_chars = _minimum_expected_body_chars(source_text)
    if minimum_chars:
        targets.append(f"- minimum useful Markdown body length: about {minimum_chars}+ characters")
    if len(source_text) >= 6000:
        targets.append(
            "- long transcript target: usually 8+ flow rows and 8+ combined "
            "3-x/4-x subsections"
        )
    return "\n".join(targets)


def _section_count_target_brief(source_text: str) -> str:
    numeric_tokens = _numeric_detail_tokens(source_text)
    if len(source_text) >= 6000:
        flow_rows = 8
        concept_sections = 6
        detail_sections = 5
        number_rows = max(10, min(len(numeric_tokens), 24))
        action_items = 8
    elif len(source_text) >= 3000:
        flow_rows = 5
        concept_sections = 4
        detail_sections = 3
        number_rows = max(5, min(len(numeric_tokens), 14))
        action_items = 5
    else:
        flow_rows = 3
        concept_sections = 2
        detail_sections = 2
        number_rows = max(3, min(len(numeric_tokens), 8)) if numeric_tokens else 0
        action_items = 3

    targets = [
        f"- lecture flow table rows: at least {flow_rows} when supported by source",
        f"- key concept subsections: at least {concept_sections} when supported by source",
        "- detailed reconstruction subsections: "
        f"at least {detail_sections} when supported by source",
        f"- practical/next action items: at least {action_items} when supported by source",
    ]
    if number_rows:
        targets.append(f"- Numbers / Examples rows: at least {number_rows} concrete rows")
    return "\n".join(targets)


def _required_markdown_skeleton(resolved_language: str = "ko") -> str:
    if resolved_language == "en":
        return (
            "# {Lecture Title}\n\n"
            "## 0. One Sentence Core\n\n"
            "## 1. Lecture Overview\n\n"
            "## 2. Lecture Flow\n\n"
            "## 3. Key Concepts\n\n"
            "## 4. Detailed Lecture Reconstruction\n\n"
            "## 5. Comparison and Structured Summary\n\n"
            "## 6. Numbers and Examples\n\n"
            "## 7. Practical Actions\n\n"
            "## 8. Mission\n\n"
            "## 9. Obsidian Connections\n\n"
            "## 10. Personal or Project Application\n\n"
            "## 11. Final Takeaways\n\n"
            "## 12. Next Actions"
        )
    return (
        "# {강의 제목}\n\n"
        "## 0. 한 문장 핵심\n\n"
        "## 1. 강의 전체 요약\n\n"
        "## 2. 강의 흐름 구조\n\n"
        "## 3. 핵심 개념 정리\n\n"
        "## 4. 강의 내용 상세 정리\n\n"
        "## 5. 비교와 구조화 정리\n\n"
        "## 6. 숫자와 사례 정리\n\n"
        "## 7. 실전 적용 방법\n\n"
        "## 8. 강의 미션 정리\n\n"
        "## 9. Obsidian 연결\n\n"
        "## 10. 개인 또는 프로젝트 적용\n\n"
        "## 11. 최종 핵심 정리\n\n"
        "## 12. 다음 액션"
    )


def _source_review_excerpts(source_text: str, max_chars: int = 2400) -> str:
    text = re.sub(r"\s+", " ", source_text).strip()
    if not text:
        return "- 원문 전체를 다시 확인하세요."
    if len(text) <= max_chars:
        return text

    excerpt_size = max_chars // 3
    middle_start = max(0, (len(text) // 2) - (excerpt_size // 2))
    ending_start = max(0, len(text) - excerpt_size)
    return "\n\n".join(
        [
            "[Beginning]\n" + text[:excerpt_size].strip(),
            "[Middle]\n" + text[middle_start : middle_start + excerpt_size].strip(),
            "[Ending]\n" + text[ending_start:].strip(),
        ]
    )


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
