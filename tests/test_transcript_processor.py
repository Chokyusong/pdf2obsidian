from __future__ import annotations

from pdf2obsidian.core.transcript_processor import read_transcript


def test_read_transcript_handles_number_prefixed_inline_timestamps(tmp_path):
    path = tmp_path / "13.md"
    path.write_text(
        "\n\n".join(
            [
                "100:00:00.000 --> 00:00:04.860안녕하세요 자동 수익 이야기입니다",
                "200:00:04.860 --> 00:00:09.800노동 수익과 자동 수익의 차이입니다",
            ]
        ),
        encoding="utf-8",
    )

    blocks = read_transcript(path)

    assert blocks
    assert blocks[0].start == "00:00:00"
    assert "안녕하세요 자동 수익 이야기입니다" in blocks[0].text
    assert "200:00" not in blocks[0].text


def test_read_transcript_parses_vtt_timestamps(tmp_path):
    path = tmp_path / "lecture.vtt"
    path.write_text(
        "\n".join(
            [
                "WEBVTT",
                "",
                "00:00:01.000 --> 00:00:03.000",
                "첫 번째 설명입니다.",
                "",
                "00:00:03.000 --> 00:00:05.000",
                "두 번째 설명입니다.",
            ]
        ),
        encoding="utf-8",
    )

    blocks = read_transcript(path)

    assert blocks[0].start == "00:00:01"
    assert "첫 번째 설명입니다" in blocks[0].text
    assert "두 번째 설명입니다" in blocks[0].text


def test_read_transcript_parses_plain_text_paragraphs(tmp_path):
    path = tmp_path / "lecture.txt"
    path.write_text("첫 번째 문단입니다.\n\n두 번째 문단입니다.", encoding="utf-8")

    blocks = read_transcript(path)

    assert len(blocks) == 1
    assert "첫 번째 문단입니다" in blocks[0].text
    assert "두 번째 문단입니다" in blocks[0].text
