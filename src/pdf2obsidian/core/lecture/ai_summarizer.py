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
    max_chars: int = 6000,
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
        emit_progress(
            10 + int(((chunk_index - 1) / total_chunks) * 45),
            f"Ollama chunk {chunk_index}/{total_chunks} started.",
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
            f"Ollama chunk {chunk_index}/{total_chunks} finished.",
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

    if _has_language_mismatch(combined, resolved_language):
        emit_progress(75, "Retrying Ollama reconstruction with language correction.")
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
        emit_progress(80, "Ollama language correction finished.")

    emit_progress(82, "Checking Ollama reconstruction quality.")
    markdown = _normalize_final_markdown(
        combined,
        title=title,
        source_type=source_type,
        source_file=source_file,
    )

    quality_issues = _final_quality_issues(markdown, source_text)
    for attempt_index in range(2):
        if not quality_issues:
            break
        emit_progress(
            85 + attempt_index * 4,
            f"Ollama quality retry {attempt_index + 1}/2 started.",
        )
        retry_prompt = _quality_retry_prompt(template, quality_issues, source_text)
        retry_input = _quality_retry_input(
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
                        f"selected language ({resolved_language}) after quality retry."
                    ),
                )
        markdown = _normalize_final_markdown(
            combined,
            title=title,
            source_type=source_type,
            source_file=source_file,
        )
        quality_issues = _final_quality_issues(markdown, source_text)
        emit_progress(
            88 + attempt_index * 4,
            f"Ollama quality retry {attempt_index + 1}/2 finished.",
        )

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
    emit_progress(100, "Ollama reconstruction finished.")
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
        "이 단계에서는 일반론이나 추상 표현만 반복하지 마세요.\n"
        "가능하면 최종 Markdown 구조를 유지하되, 이 청크에 없는 내용은 억지로 채우지 마세요.\n"
    )


def _merge_reconstruction_prompt(
    template: str,
    resolved_language: str,
    source_text: str,
) -> str:
    coverage_brief = _source_coverage_brief(source_text)
    if resolved_language != "ko":
        return (
            f"{template}\n\n"
            "Merge stage: combine the chunk notes into one final Obsidian Markdown study "
            "note. Preserve details from every chunk. Do not summarize away examples, "
            "numbers, missions, or action steps.\n\n"
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
        "반복은 제거하되 세부 정보는 삭제하지 마세요.\n"
        "일반 문장 반복으로 분량을 채우지 마세요.\n"
        "청크에 덜 다듬어진 자막 문장이 있더라도 원문 덩어리로 붙이지 말고 "
        "자연스러운 설명 문장으로 재작성하세요.\n"
        "출력은 반드시 `# 강의 제목`, `## 0. 한 줄 핵심`부터 시작되는 완성본이어야 합니다.\n"
        "중간 섹션만 출력하거나 0~3번 섹션을 생략하면 실패입니다.\n"
        "최종 Markdown은 반드시 0번부터 12번 섹션까지만 사용하세요.\n"
        "아래 보존 우선순위를 최종본의 관련 섹션에 자연스럽게 녹이세요.\n\n"
        f"보존 우선순위:\n{coverage_brief}\n"
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
    return _structure_quality_issues(
        markdown,
        source_text,
    ) + _coverage_quality_issues(markdown, source_text)


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


def _coverage_quality_issues(markdown: str, source_text: str) -> list[str]:
    if len(source_text) < 1000:
        return []

    body = _content_without_frontmatter(markdown)
    min_expected_chars = min(4000, max(1200, int(len(source_text) * 0.18)))
    if len(body) < min_expected_chars:
        return [
            "generated Markdown is too short for the source transcript "
            f"({len(body)} chars, expected at least {min_expected_chars})"
        ]
    return []


def _quality_retry_prompt(
    template: str,
    quality_issues: list[str],
    source_text: str,
) -> str:
    issue_list = "\n".join(f"- {issue}" for issue in quality_issues)
    coverage_brief = _source_coverage_brief(source_text)
    return (
        f"{template}\n\n"
        "중요: 이전 출력은 범용 강의 재구성 품질 기준을 충족하지 못했습니다.\n"
        "이번에는 현재 Markdown을 기반으로 전체 문서를 다시 완성하세요.\n"
        "아래 수정 항목을 반드시 해결하고, 원문에 있는 핵심 개념, 숫자, "
        "예시, 절차, 과제, 주의사항을 관련 본문 섹션에 자연스럽게 반영하세요.\n"
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
        "보존 우선순위:\n"
        f"{coverage_brief}\n\n"
        "반드시 사용할 최종 Markdown 골격:\n"
        f"{_required_markdown_skeleton()}\n\n"
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
    return len(quality_issues) >= 8 or any("필수 섹션 누락" in issue for issue in quality_issues)


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
    return "\n".join(priorities)


def _required_markdown_skeleton() -> str:
    return (
        "# {강의 제목}\n\n"
        "## 0. One Sentence Core / 한 문장 핵심\n\n"
        "## 1. Lecture Overview / 강의 전체 요약\n\n"
        "## 2. Lecture Flow / 강의 흐름 구조\n\n"
        "## 3. Key Concepts / 핵심 개념 정리\n\n"
        "## 4. Detailed Lecture Reconstruction / 강의 내용 상세 정리\n\n"
        "## 5. Comparison / Structured Summary / 비교와 구조화 정리\n\n"
        "## 6. Numbers / Examples / 숫자와 사례 정리\n\n"
        "## 7. Practical Actions / 실전 적용 방법\n\n"
        "## 8. Mission / 강의 미션 정리\n\n"
        "## 9. Obsidian Connections / Obsidian 연결\n\n"
        "## 10. Personal / Project Application / 개인 또는 프로젝트 적용\n\n"
        "## 11. Final Takeaways / 최종 핵심 정리\n\n"
        "## 12. Next Actions / 다음 액션"
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
