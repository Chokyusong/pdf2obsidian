from __future__ import annotations

from datetime import date

from pdf2obsidian.core.lecture_note_writer import write_lecture_note
from pdf2obsidian.core.transcript_processor import TranscriptBlock


def _blocks() -> list[TranscriptBlock]:
    return [
        TranscriptBlock(
            start="00:00:00",
            end="00:01:00",
            text="오늘은 로컬 OCR 설정 방법을 설명합니다. 먼저 PDF를 준비합니다.",
        ),
        TranscriptBlock(
            start="00:01:00",
            end="00:02:00",
            text="다음 단계에서는 Markdown 변환 결과를 확인합니다. 중요한 설정은 품질 값입니다.",
        ),
        TranscriptBlock(
            start="00:02:00",
            end="00:03:00",
            text="주의할 점은 원문에 없는 내용을 추가하지 않는 것입니다.",
        ),
    ]


def test_study_note_applies_timestamps_questions_and_checklist(tmp_path):
    output = tmp_path / "note.md"

    write_lecture_note(
        output,
        title="lecture",
        source_file="lecture.srt",
        blocks=_blocks(),
        output_format="study_note",
        keep_timestamps=True,
        include_review_questions=True,
        include_checklist=True,
        created=date(2026, 6, 25),
    )

    content = output.read_text(encoding="utf-8")

    assert 'type: "lecture-study-note"' in content
    assert "### 00:00:00 - 00:03:00" in content
    assert "## 복습 질문" in content
    assert "## 실행 체크리스트" in content
    assert "- [ ] 먼저 PDF를 준비합니다." in content


def test_study_note_can_omit_timestamps_questions_and_checklist(tmp_path):
    output = tmp_path / "note.md"

    write_lecture_note(
        output,
        title="lecture",
        source_file="lecture.srt",
        blocks=_blocks(),
        output_format="study_note",
        keep_timestamps=False,
        include_review_questions=False,
        include_checklist=False,
    )

    content = output.read_text(encoding="utf-8")

    assert "### 00:00:00" not in content
    assert "## 복습 질문" not in content
    assert "## 실행 체크리스트" not in content


def test_output_formats_are_distinct(tmp_path):
    study = tmp_path / "study.md"
    ebook = tmp_path / "ebook.md"
    moc = tmp_path / "moc.md"

    write_lecture_note(study, "lecture", "lecture.vtt", _blocks(), output_format="study_note")
    write_lecture_note(ebook, "lecture", "lecture.vtt", _blocks(), output_format="ebook_draft")
    write_lecture_note(moc, "lecture", "lecture.vtt", _blocks(), output_format="obsidian_moc")

    study_content = study.read_text(encoding="utf-8")
    ebook_content = ebook.read_text(encoding="utf-8")
    moc_content = moc.read_text(encoding="utf-8")

    assert 'type: "lecture-study-note"' in study_content
    assert 'type: "lecture-ebook-draft"' in ebook_content
    assert 'type: "obsidian-moc"' in moc_content
    assert "## 원고 초안" in ebook_content
    assert "## 노트 후보" in moc_content


def test_no_topic_specific_hardcoded_auto_income_output(tmp_path):
    output = tmp_path / "note.md"
    blocks = [
        TranscriptBlock(
            start="00:00:00",
            end="00:01:00",
            text="자동 수익이라는 표현이 있어도 제품 코드는 샘플 강의용 문장을 만들면 안 됩니다.",
        )
    ]

    write_lecture_note(output, "lecture", "lecture.srt", blocks, output_format="study_note")

    content = output.read_text(encoding="utf-8")

    assert "노동 수익만으로는 장기적인 자유를 얻기 어렵기 때문에" not in content
    assert "첫 디지털 자산을 만든다" not in content
