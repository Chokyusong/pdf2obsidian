from __future__ import annotations

import shutil
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont

from pdf2obsidian.core.converter import ConversionOptions, convert_file

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "docs" / "samples"
DEMO_OUTPUT = ROOT / "docs" / "demo-output"
TEMP_OUTPUT = ROOT / ".tmp" / "demo-conversion"
ASSET_DIR = ROOT / "docs" / "assets"

PDF_PATH = SAMPLE_DIR / "sample_course.pdf"
VTT_PATH = SAMPLE_DIR / "sample_lecture.vtt"
PDF_PREVIEW = ASSET_DIR / "sample-course-cover.png"


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _demo_image(index: int, title: str, color: tuple[int, int, int]) -> bytes:
    image = Image.new("RGB", (640, 300), (248, 249, 251))
    draw = ImageDraw.Draw(image)
    title_font = _font(32)
    body_font = _font(20)
    small_font = _font(16)

    draw.rounded_rectangle(
        (24, 24, 616, 276), radius=18, fill=(255, 255, 255), outline=color, width=4
    )
    draw.rectangle((24, 24, 616, 88), fill=color)
    draw.text((54, 44), f"Synthetic diagram {index}", fill=(255, 255, 255), font=small_font)
    draw.text((54, 116), title, fill=(31, 41, 55), font=title_font)
    draw.text((54, 174), "Safe README demo asset", fill=(75, 85, 99), font=body_font)
    draw.text(
        (54, 214), "No real course, PDF, transcript, or user data.", fill=color, font=body_font
    )

    from io import BytesIO

    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=86, optimize=True)
    return buffer.getvalue()


def _heading(page: fitz.Page, text: str, y: int = 64) -> None:
    page.insert_text((54, y), text, fontsize=22, fontname="helv", color=(0.08, 0.1, 0.14))


def _body(page: fitz.Page, rect: fitz.Rect, text: str, size: int = 11) -> None:
    page.insert_textbox(
        rect, text, fontsize=size, fontname="helv", color=(0.14, 0.16, 0.2), lineheight=1.25
    )


def _footer(page: fitz.Page, page_number: int, total: int) -> None:
    page.insert_text(
        (456, 792), f"Page {page_number} / {total}", fontsize=10, color=(0.35, 0.38, 0.43)
    )


def _insert_image(page: fitz.Page, rect: fitz.Rect, image: bytes) -> None:
    page.insert_image(rect, stream=image)


def _draw_table(page: fitz.Page) -> None:
    rows = [
        ("Input", "Expected Markdown result"),
        ("PDF heading", "## or ### heading"),
        ("Simple table", "Markdown table"),
        ("Embedded image", "WebP asset reference"),
        ("Complex table", "WebP fallback image"),
    ]
    x0, y0, col_w, row_h = 54, 188, 235, 42
    for row_index, row in enumerate(rows):
        y = y0 + row_index * row_h
        fill = (0.9, 0.94, 1.0) if row_index == 0 else (1, 1, 1)
        page.draw_rect(
            fitz.Rect(x0, y, x0 + col_w * 2, y + row_h), fill=fill, color=(0.78, 0.81, 0.86)
        )
        page.draw_line((x0 + col_w, y), (x0 + col_w, y + row_h), color=(0.78, 0.81, 0.86))
        page.insert_text((x0 + 12, y + 26), row[0], fontsize=11)
        page.insert_text((x0 + col_w + 12, y + 26), row[1], fontsize=11)


def create_sample_pdf() -> None:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    total_pages = 5
    images = [
        _demo_image(1, "Local-first overview", (37, 99, 235)),
        _demo_image(2, "Table of contents map", (5, 150, 105)),
        _demo_image(3, "PDF conversion flow", (124, 58, 237)),
        _demo_image(4, "Markdown table target", (234, 88, 12)),
        _demo_image(5, "Lecture note checklist", (220, 38, 38)),
    ]

    page = doc.new_page(width=595, height=842)
    page.insert_text(
        (54, 82), "Sample Course Pack", fontsize=30, fontname="helv", color=(0.08, 0.1, 0.14)
    )
    page.insert_text(
        (54, 122),
        "Synthetic PDF for PDF2Obsidian README demos",
        fontsize=14,
        color=(0.35, 0.38, 0.43),
    )
    _body(
        page,
        fitz.Rect(54, 166, 540, 250),
        "This document is generated for open-source documentation. It contains a cover, "
        "table of contents, body sections, a simple table, a checklist, links, and five "
        "synthetic diagrams.",
        12,
    )
    _insert_image(page, fitz.Rect(54, 292, 541, 520), images[0])
    _body(
        page,
        fitz.Rect(54, 570, 540, 642),
        "Privacy note: this sample contains no real lecture title, no paid PDF content, "
        "no private note path, and no copied transcript text.",
        11,
    )
    _footer(page, 1, total_pages)

    page = doc.new_page(width=595, height=842)
    _heading(page, "Table of Contents")
    toc_lines = [
        "1. Local-first conversion workflow",
        "2. PDF to Obsidian Markdown",
        "3. Table and image handling",
        "4. Lecture transcript study notes",
        "5. Review checklist",
    ]
    y = 122
    for line in toc_lines:
        page.insert_text((72, y), line, fontsize=13)
        y += 34
    _insert_image(page, fitz.Rect(54, 340, 541, 568), images[1])
    _body(
        page,
        fitz.Rect(54, 610, 540, 682),
        "The table of contents gives the converter headings, ordered content, and page "
        "boundaries to preserve in Markdown.",
        11,
    )
    _footer(page, 2, total_pages)

    page = doc.new_page(width=595, height=842)
    _heading(page, "1. Local-first Conversion Workflow")
    _body(
        page,
        fitz.Rect(54, 104, 540, 206),
        "PDF2Obsidian reads files from local disk and writes Markdown to a local output folder. "
        "The basic conversion path does not require login, cloud upload, or external AI APIs. "
        "This section gives the converter paragraphs and a meaningful diagram.",
        12,
    )
    page.insert_text((72, 250), "- Choose a PDF, image, or transcript file.", fontsize=12)
    page.insert_text((72, 282), "- Convert the file into Markdown and WebP assets.", fontsize=12)
    page.insert_text((72, 314), "- Move the generated folder into an Obsidian vault.", fontsize=12)
    _insert_image(page, fitz.Rect(54, 380, 541, 608), images[2])
    _footer(page, 3, total_pages)

    page = doc.new_page(width=595, height=842)
    _heading(page, "2. PDF to Obsidian Markdown")
    _body(
        page,
        fitz.Rect(54, 104, 540, 168),
        "The converter restores searchable text, headings, lists, simple tables, links, "
        "and embedded images where practical.",
        12,
    )
    _draw_table(page)
    _insert_image(page, fitz.Rect(54, 440, 541, 668), images[3])
    page.insert_text(
        (54, 714),
        "Reference: https://example.org/pdf2obsidian-sample",
        fontsize=11,
        color=(0.1, 0.25, 0.75),
    )
    page.insert_link(
        {
            "kind": fitz.LINK_URI,
            "from": fitz.Rect(54, 700, 340, 724),
            "uri": "https://example.org/pdf2obsidian-sample",
        }
    )
    _footer(page, 4, total_pages)

    page = doc.new_page(width=595, height=842)
    _heading(page, "3. Lecture Notes and Review Checklist")
    _body(
        page,
        fitz.Rect(54, 104, 540, 180),
        "Lecture subtitles can be converted into a study note with overview, key concepts, "
        "timeline sections, review questions, and an execution checklist.",
        12,
    )
    checklist = [
        "Check that Markdown headings are readable.",
        "Check that image links open in Obsidian.",
        "Check that table content is not lost.",
        "Check that the conversion report has no warnings.",
        "Check that only synthetic documentation samples are committed.",
    ]
    y = 230
    for item in checklist:
        page.insert_text((72, y), f"- [ ] {item}", fontsize=12)
        y += 32
    _insert_image(page, fitz.Rect(54, 432, 541, 660), images[4])
    _footer(page, 5, total_pages)

    doc.save(PDF_PATH, deflate=True, garbage=4)
    doc.close()

    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    preview_doc = fitz.open(PDF_PATH)
    pix = preview_doc[0].get_pixmap(matrix=fitz.Matrix(1.4, 1.4), alpha=False)
    pix.save(PDF_PREVIEW)
    preview_doc.close()


def _vtt_cues() -> list[str]:
    phases = [
        (
            "Introduction",
            12,
            "The Obsidian workflow starts with a local source file and a clear conversion goal.",
        ),
        (
            "Introduction",
            8,
            "The privacy model keeps the sample PDF and sample transcript on the user's computer.",
        ),
        (
            "Key concept",
            16,
            "Markdown conversion creates editable notes, stable headings, and reusable wiki links.",
        ),
        (
            "Key concept",
            12,
            "The PDF conversion pipeline extracts text, tables, links, and meaningful WebP assets.",
        ),
        (
            "Example",
            14,
            "For example, a simple table becomes a Markdown table in the converted note.",
        ),
        (
            "Example",
            10,
            "For example, a complex diagram remains a WebP asset so information is not lost.",
        ),
        (
            "Practice",
            14,
            "First choose sample_course.pdf, then run the Markdown and image conversion output.",
        ),
        (
            "Practice",
            10,
            "Next choose sample_lecture.vtt, then run the lecture transcript study note output.",
        ),
        (
            "Summary",
            8,
            "The review step checks headings, assets, table output, and the conversion report.",
        ),
        ("Review question", 4, "Which part of the Obsidian workflow protects the privacy model?"),
        (
            "Mission",
            2,
            "Your mission is to convert the sample files and inspect the generated Markdown.",
        ),
    ]
    cues: list[str] = []
    for phase, count, sentence in phases:
        for _index in range(1, count + 1):
            cues.append(f"{phase}: {sentence}")
    return cues[:100]


def create_sample_vtt() -> None:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    lines = ["WEBVTT", ""]
    for index, text in enumerate(_vtt_cues(), start=1):
        offset = (index - 1) * 4
        start_minutes = offset // 60
        start_seconds = offset % 60
        end_offset = offset + 4
        end_minutes = end_offset // 60
        end_seconds = end_offset % 60
        lines.extend(
            [
                str(index),
                f"00:{start_minutes:02d}:{start_seconds:02d}.000 --> "
                f"00:{end_minutes:02d}:{end_seconds:02d}.000",
                text,
                "",
            ]
        )
    VTT_PATH.write_text("\n".join(lines), encoding="utf-8")


def _copy_selected_demo_output() -> None:
    if DEMO_OUTPUT.exists():
        shutil.rmtree(DEMO_OUTPUT)
    DEMO_OUTPUT.mkdir(parents=True, exist_ok=True)

    source_pdf_dir = TEMP_OUTPUT / "sample_course"
    source_lecture_dir = TEMP_OUTPUT / "sample_lecture"
    pdf_markdown = (source_pdf_dir / "sample_course.md").read_text(encoding="utf-8")
    pdf_markdown = pdf_markdown.replace(
        "![[Files/sample_course/",
        "![[assets/sample_course/",
    )
    (DEMO_OUTPUT / "sample_course.md").write_text(pdf_markdown, encoding="utf-8")
    shutil.copy2(source_lecture_dir / "sample_lecture.md", DEMO_OUTPUT / "sample_lecture.md")

    source_assets = source_pdf_dir / "Files" / "sample_course"
    target_assets = DEMO_OUTPUT / "assets" / "sample_course"
    target_assets.mkdir(parents=True, exist_ok=True)
    for asset in sorted(source_assets.glob("*.webp")):
        shutil.copy2(asset, target_assets / asset.name)


def build_demo_output() -> None:
    if TEMP_OUTPUT.exists():
        shutil.rmtree(TEMP_OUTPUT)
    TEMP_OUTPUT.mkdir(parents=True, exist_ok=True)
    options = ConversionOptions(
        output_root=TEMP_OUTPUT,
        image_quality=75,
        mode="auto",
        transcript_preserve_level="medium",
        transcript_output_format="study_note",
    )
    convert_file(PDF_PATH, options)
    convert_file(VTT_PATH, options)
    _copy_selected_demo_output()


def main() -> None:
    create_sample_pdf()
    create_sample_vtt()
    build_demo_output()
    print(f"Created {PDF_PATH.relative_to(ROOT)}")
    print(f"Created {VTT_PATH.relative_to(ROOT)}")
    print(f"Created {PDF_PREVIEW.relative_to(ROOT)}")
    print(f"Created {DEMO_OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
