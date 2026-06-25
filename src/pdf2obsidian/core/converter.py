from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from pdf2obsidian.core.image_processor import save_image_as_webp
from pdf2obsidian.core.lecture_note_writer import write_lecture_note
from pdf2obsidian.core.markdown_writer import (
    write_image_markdown,
    write_pdf_markdown,
)
from pdf2obsidian.core.pdf_compressor import compress_pdf_to_webp_pdf
from pdf2obsidian.core.pdf_processor import process_pdf
from pdf2obsidian.core.transcript_processor import read_transcript
from pdf2obsidian.utils.paths import (
    is_image,
    is_pdf,
    is_supported,
    is_transcript,
    make_output_paths,
    sanitize_filename,
)

LogCallback = Callable[[str], None]
ProgressCallback = Callable[[int, int], None]


@dataclass(frozen=True)
class ConversionOptions:
    output_root: Path
    image_quality: int = 75
    ocr_enabled: bool = False
    include_page_separator: bool = True
    mode: str = "auto"
    pdf_output_format: str = "markdown_image"
    transcript_preserve_level: str = "medium"
    transcript_output_format: str = "study_note"
    transcript_keep_timestamps: bool = True
    transcript_review_questions: bool = True
    transcript_checklist: bool = True


@dataclass(frozen=True)
class ConversionResult:
    source_path: Path
    output_dir: Path
    markdown_path: Path
    kind: str


def _title_for(source: Path) -> str:
    return sanitize_filename(source.stem)


def _format_bytes(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def convert_file(
    input_path: str | Path,
    options: ConversionOptions,
    log: LogCallback | None = None,
) -> ConversionResult:
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(f"Input file does not exist: {source}")
    if not is_supported(source):
        raise ValueError(f"Unsupported file type: {source.suffix}")

    title = _title_for(source)
    item_dir, assets_dir, markdown_path = make_output_paths(source, options.output_root)

    def emit(message: str) -> None:
        if log:
            log(message)

    if is_pdf(source):
        if options.mode == "lecture":
            raise ValueError("PDF files cannot be converted in lecture transcript mode.")

        if options.pdf_output_format == "webp_compression":
            emit(f"Compressing PDF: {source.name}")
            compression_result = compress_pdf_to_webp_pdf(
                source,
                item_dir,
                quality=options.image_quality,
            )
            reduction = compression_result.size_reduction_percent
            reduction_text = "unknown" if reduction is None else f"{reduction:.1f}%"
            emit(
                "PDF compression result: "
                f"{_format_bytes(compression_result.source_size_bytes)} -> "
                f"{_format_bytes(compression_result.output_size_bytes)} "
                f"({reduction_text} smaller)"
            )
            return ConversionResult(
                source,
                item_dir,
                compression_result.output_path,
                "pdf_compression",
            )

        emit(f"Processing PDF: {source.name}")
        pdf_assets_dir = item_dir / "Files" / title
        pdf_assets_dir.mkdir(parents=True, exist_ok=True)
        pdf_result = process_pdf(
            source,
            pdf_assets_dir,
            quality=options.image_quality,
            ocr_enabled=options.ocr_enabled,
        )
        write_pdf_markdown(
            markdown_path,
            title=title,
            source_file=source.name,
            pdf_result=pdf_result,
            include_page_separator=options.include_page_separator,
            asset_link_prefix=f"Files/{title}",
        )
        return ConversionResult(source, item_dir, markdown_path, "pdf")

    if is_image(source):
        if options.mode == "lecture":
            raise ValueError("Image files cannot be converted in lecture transcript mode.")
        emit(f"Processing image: {source.name}")
        image_result = save_image_as_webp(
            source,
            assets_dir,
            quality=options.image_quality,
            ocr_enabled=options.ocr_enabled,
        )
        write_image_markdown(
            markdown_path,
            title=title,
            source_file=source.name,
            image_result=image_result,
        )
        return ConversionResult(source, item_dir, markdown_path, "image")

    if is_transcript(source):
        if options.mode == "pdf_image":
            raise ValueError("Transcript files cannot be converted in PDF/Image mode.")
        emit(f"Processing transcript: {source.name}")
        blocks = read_transcript(source)
        write_lecture_note(
            markdown_path,
            title=title,
            source_file=source.name,
            blocks=blocks,
            preserve_level=options.transcript_preserve_level,
            output_format=options.transcript_output_format,
            keep_timestamps=options.transcript_keep_timestamps,
            include_review_questions=options.transcript_review_questions,
            include_checklist=options.transcript_checklist,
        )
        return ConversionResult(source, item_dir, markdown_path, "transcript")

    raise ValueError(f"Unsupported file type: {source.suffix}")


def convert_files(
    input_paths: list[str | Path],
    options: ConversionOptions,
    log: LogCallback | None = None,
    progress: ProgressCallback | None = None,
) -> list[ConversionResult]:
    results: list[ConversionResult] = []
    total = len(input_paths)

    for index, input_path in enumerate(input_paths, start=1):
        result = convert_file(input_path, options, log=log)
        results.append(result)
        if progress:
            progress(index, total)

    return results
