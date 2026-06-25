from __future__ import annotations

from io import BytesIO

import fitz
from PIL import Image, ImageDraw

from pdf2obsidian.core.converter import ConversionOptions, convert_file


def _sample_png_bytes() -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (240, 180), color=(40, 120, 200))
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 20, 220, 80), fill=(20, 20, 40))
    draw.rectangle((40, 105, 180, 150), fill=(240, 120, 40))
    draw.text((52, 118), "PDF IMAGE", fill=(255, 255, 255))
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_pdf_conversion_uses_files_folder_and_manage_pdf_profile(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    output_root = tmp_path / "output"

    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 72), "Main Heading", fontsize=22)
    page.insert_image(fitz.Rect(72, 120, 312, 300), stream=_sample_png_bytes())
    document.save(pdf_path)
    document.close()

    result = convert_file(pdf_path, ConversionOptions(output_root=output_root))

    markdown = result.markdown_path.read_text(encoding="utf-8")
    expected_asset = result.output_dir / "Files" / "sample" / "p001-img01.webp"

    assert expected_asset.exists()
    assert "![[Files/sample/p001-img01.webp]]" in markdown
    assert "Conversion profile: manage-pdf-in-obsidian" in markdown
    assert "page_001.webp" not in markdown


def test_pdf_webp_compression_creates_compressed_pdf_and_report(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    output_root = tmp_path / "output"

    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 72), "Compression sample", fontsize=18)
    page.insert_image(fitz.Rect(72, 120, 312, 300), stream=_sample_png_bytes())
    document.save(pdf_path)
    document.close()

    result = convert_file(
        pdf_path,
        ConversionOptions(
            output_root=output_root,
            pdf_output_format="webp_compression",
            image_quality=60,
        ),
    )

    compressed_pdf = result.output_dir / "sample-compressed.pdf"
    report = result.output_dir / "sample-compression-report.md"

    assert result.kind == "pdf_compression"
    assert result.markdown_path == compressed_pdf
    assert compressed_pdf.exists()
    assert report.exists()
    assert "PDF Compression Report" in report.read_text(encoding="utf-8")

    with fitz.open(compressed_pdf) as compressed:
        assert compressed.page_count == 1
