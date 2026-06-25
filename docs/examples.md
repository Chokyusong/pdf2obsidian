# PDF2Obsidian Examples

This page shows the intended output style for the first MVP. The application keeps all conversion work on the user's computer.

Private or paid learning materials must not be committed as examples. Sample files should be synthetic, public-domain, openly licensed, or explicitly redistributable.

## Reproducible Demo Samples

The repository includes two safe synthetic inputs that were generated for documentation:

- `docs/samples/sample_course.pdf`
- `docs/samples/sample_lecture.vtt`

The selected demo conversion output is stored under:

```text
docs/demo-output/
├─ sample_course.md
├─ sample_lecture.md
└─ assets/
   └─ sample_course/
      ├─ p001-img01.webp
      ├─ p002-img01.webp
      ├─ p003-img01.webp
      ├─ p004-img01.webp
      └─ p005-img01.webp
```

These files are synthetic samples only. They do not use real lecture names, real PDF titles, copied subtitle text, personal paths, or paid learning material.

### PDF Before

Input file:

```text
docs/samples/sample_course.pdf
```

Before conversion, the PDF contains:

```text
sample_course.pdf
├─ Page 1: cover and synthetic diagram
├─ Page 2: table of contents and synthetic diagram
├─ Page 3: body section with bullets and synthetic diagram
├─ Page 4: body section with one simple table, link, and synthetic diagram
└─ Page 5: lecture note checklist and synthetic diagram
```

### PDF After

Selected Markdown output:

```text
docs/demo-output/sample_course.md
```

Markdown excerpt:

```markdown
# sample_course

<p align="center"><sub>PDF 4페이지</sub></p>

## 2. PDF to Obsidian Markdown

##### Table 1

| Input | Expected Markdown result |
| --- | --- |
| PDF heading | ## or ### heading |
| Simple table | Markdown table |
| Embedded image | WebP asset reference |
| Complex table | WebP fallback image |

##### Image 1

![[assets/sample_course/p004-img01.webp]]

##### Links

- [https://example.org/pdf2obsidian-sample](https://example.org/pdf2obsidian-sample)
```

In Obsidian, this appears as one editable Markdown note with page markers, headings, a Markdown table, rendered WebP images, and a conversion report at the bottom.

### Lecture Transcript Before

Input file:

```text
docs/samples/sample_lecture.vtt
```

Before conversion, the VTT contains about 100 timestamped cues:

```text
WEBVTT

1
00:00:00.000 --> 00:00:04.000
Introduction: The Obsidian workflow starts with a local source file and a clear conversion goal.

2
00:00:04.000 --> 00:00:08.000
Introduction: The Obsidian workflow starts with a local source file and a clear conversion goal.
```

The synthetic transcript flow covers introduction, key concepts, examples, practice, summary, review questions, and mission.

### Lecture Transcript After

Selected Markdown output:

```text
docs/demo-output/sample_lecture.md
```

Markdown excerpt:

```markdown
## 강의 개요

- Introduction: The Obsidian workflow starts with a local source file and a clear conversion goal.

## 핵심 개념

- **conversion**: Introduction: The Obsidian workflow starts with a local source file and a clear conversion goal.
- **Markdown**: Key concept: Markdown conversion creates editable notes, stable headings, and reusable wiki links.

## 강의 흐름

### 00:00:00 - 00:01:00

Introduction: The Obsidian workflow starts with a local source file and a clear conversion goal.
```

In Obsidian, this appears as a study note with overview, key concepts, timestamped sections, review questions, and checklist content when action sentences are detected.

## PDF Import

Input:

```text
sample.pdf
```

Before conversion:

```text
sample.pdf
├─ Page 1: document title, two paragraphs, and one embedded diagram
├─ Page 2: a simple table
└─ Page 3: a source URL
```

Output:

```text
output/
└─ sample/
   ├─ sample.md
   └─ Files/
      └─ sample/
         └─ p001-img01.webp
```

Markdown:

```markdown
---
title: "sample"
source_file: "sample.pdf"
created: "2026-06-25"
type: "pdf-import"
---

# sample

<p align="center"><sub>PDF 1페이지</sub></p>

Extracted PDF text appears here.

##### Image 1

![[Files/sample/p001-img01.webp]]

## Conversion Report

- Source pages: 3
- Extracted text characters: 12000
- Markdown tables: 1
- Extracted PDF images: 1
- Verification: text layer extraction was attempted before OCR.
- Conversion profile: manage-pdf-in-obsidian
- Verification: full PDF pages are not inserted as default images.
- Verification: only necessary PDF images and table-region fallbacks are saved.
```

After conversion, the Markdown is editable and the image assets are linked with Obsidian wiki links. The original PDF is not copied into the output folder.

## Image Import

Input:

```text
diagram.png
```

Before conversion:

```text
diagram.png
└─ A public or synthetic diagram image
```

Output:

```text
output/
└─ diagram/
   ├─ diagram.md
   └─ assets/
      └─ image_001.webp
```

Markdown:

```markdown
---
title: "diagram"
source_file: "diagram.png"
created: "2026-06-25"
type: "image-import"
---

# diagram

![[assets/image_001.webp]]

Optional OCR text appears here when local OCR is enabled.
```

## PDF Compression

Input:

```text
sample.pdf
```

Output:

```text
output/
└─ sample/
   ├─ sample-compressed.pdf
   └─ sample-compression-report.md
```

The compressed PDF output rasterizes pages and rebuilds a smaller PDF. It is intended for file-size reduction, not editable Markdown.

## Lecture Transcript Import

Input:

```text
lecture.vtt
```

Before conversion:

```text
lecture.vtt
└─ Short synthetic subtitle blocks with timestamps
```

Output:

```text
output/
└─ lecture/
   ├─ lecture.md
   └─ assets/
```

Markdown:

```markdown
---
title: "lecture"
source_file: "lecture.vtt"
created: "2026-06-25"
type: "lecture-transcript"
output_format: "study_note"
---

# lecture

## 1. 강의 개요

- 자막 내용을 기반으로 강의 흐름을 정리합니다.

## 2. 핵심 개념 정리

### 개념 1: Obsidian

- Obsidian 관련 내용을 강의 흐름에서 확인합니다.

## 3. 강의 흐름별 상세 정리

### 00:00:00 - 도입

Cleaned and reorganized transcript text appears here in timestamp order.

## 6. 바로 실행할 체크리스트

- [ ] 핵심 내용을 내 노트에 적용한다.

## 7. 복습 질문

1. 이 개념을 내 작업에 어떻게 적용할 수 있는가?
```

### Future Lecture Structuring Example

This synthetic example shows a known MVP limitation and the target direction. Do not use real paid lectures, instructor names, private transcripts, or user-uploaded course text as examples.

Bad example:

```markdown
- Core concepts: "여러분의", "목표를", "시스템을"
```

Good example:

```markdown
- Core concepts:
  - RAS / 망상활성계
  - 정보 필터링
  - 목표 설정
  - 뇌 내비게이션
  - 실행 행동
```

## Local-First Privacy Model

- Files are read from the local disk.
- Output is written to a local output folder.
- The app does not require login.
- The app does not upload files to a cloud server.
- The app does not require OpenAI, Claude, Gemini, or other external AI APIs.
