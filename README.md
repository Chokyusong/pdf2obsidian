# PDF2Obsidian

🇺🇸 English | 🇰🇷 [한국어](README_ko.md)

[![CI](https://github.com/Chokyusong/pdf2obsidian/actions/workflows/ci.yml/badge.svg)](https://github.com/Chokyusong/pdf2obsidian/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Chokyusong/pdf2obsidian)](https://github.com/Chokyusong/pdf2obsidian/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

PDF2Obsidian is a local-first open-source desktop tool for Obsidian users and learning-material managers. It converts PDF, image, and lecture subtitle files into Obsidian-ready Markdown and lightweight assets.

It is designed for Windows users who want to keep their files on their own computer. The app does not upload files to a server and does not use external AI APIs such as OpenAI, Claude, or Gemini.

![PDF2Obsidian GUI](docs/assets/gui-screenshot.png)

## Project Goal

PDF2Obsidian helps students, researchers, and knowledge workers turn static learning material into reusable Obsidian notes. The first MVP focuses on reliable local conversion instead of cloud automation:

- PDF text layers become lightweight Markdown.
- PDF structure is restored as editable Markdown where practical.
- Embedded PDF images become compressed WebP assets.
- Images become compressed WebP assets plus Markdown.
- Lecture subtitles become structured study notes.
- Optional OCR runs only with locally installed OCR tools.

## Final Product Vision

The long-term goal is focused on two workflows:

1. Convert PDF files into Markdown without drifting away from the original visual layout.
2. Convert lecture or YouTube subtitles into detailed study material that can replace watching the original lecture.

The default workflow should stay different from cloud AI products. PDF2Obsidian should not require external AI APIs or required cloud uploads. Advanced AI features should be optional and user-controlled through local tools.

Target capabilities:

- PDF conversion: layout-aware text extraction, heading/list/table restoration, embedded image extraction, table-region fallbacks, and Obsidian Markdown output.
- Subtitle conversion: SRT/VTT/TXT/MD parsing, repeated speech cleanup, lecture-flow preservation, concept explanation, examples, procedures, cautions, and final summary.
- YouTube subtitle workflow: import downloaded YouTube subtitles first; direct URL support can be added later.
- Output: Markdown folder with assets, ready to move into an Obsidian vault.

## Why This Exists

Many PDF notes, lecture images, and subtitles are difficult to reuse in Obsidian. This project creates a simple local workflow:

1. Select a PDF, image, or subtitle file.
2. Convert pages or images to compressed WebP assets.
3. Generate Markdown with Obsidian wiki-style image links.
4. Open the output folder and move the result into your vault.

## Target Users

- Obsidian users who want reusable Markdown instead of static PDFs.
- Students who organize class PDFs, diagrams, and lecture subtitles.
- Researchers who need local conversion without sending documents to a server.
- Knowledge workers who maintain personal knowledge bases.
- Lecture material managers who prepare searchable study notes from local files.

PDF2Obsidian should remain usable without OpenAI, Claude, Gemini, or any external AI API.

## Main Features

- Convert PDF files to Markdown.
- Compress PDF files into rasterized, smaller PDFs as a separate output mode.
- Extract PDF page text with PyMuPDF.
- Infer simple headings, bold text, lists, and paragraphs from PDF text blocks.
- Convert detected PDF tables into Markdown tables.
- Extract embedded PDF images as compressed WebP assets.
- Convert PDFs with the single `manage-pdf-in-obsidian` profile.
- Convert PNG, JPG, JPEG, and WebP images to compressed WebP.
- Optional OCR wrapper with EasyOCR first and Tesseract fallback.
- Convert SRT, VTT, TXT, and MD lecture transcripts into structured learning notes.
- Preserve lecture timestamp order when available.
- Generate Obsidian-friendly Markdown.
- Minimal PySide6 desktop GUI with drag and drop.
- Core conversion logic is separated from GUI code for future CLI or web app use.

## Quick Links

- [Examples](docs/examples.md)
- [Roadmap](docs/roadmap.md)
- [Maintenance tasks](docs/maintenance.md)
- [Web app plan](docs/webapp-plan.md)
- [Contributing](CONTRIBUTING.md)

## Installation

Python 3.11 or later is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

The `requirements.txt` file installs the local package in editable mode, so this command works from the project root:

```powershell
python -m pdf2obsidian.main
```

## Usage

1. Run the app.
2. Add PDF, image, or subtitle files with the file button or drag and drop.
3. Choose an output folder.
4. Choose image quality: 60, 75, or 90.
5. In `PDF/Image conversion` mode, choose `Markdown + Image` or `WebP Compression`.
6. Enable OCR only when you have a local OCR engine installed.
7. Click `Start Conversion`.
8. Open the output folder after conversion.

Default output is created under:

```text
output/
```

## Obsidian Output Example

For `sample.pdf`:

```text
output/
└─ sample/
   ├─ sample.md
   └─ Files/
      └─ sample/
         ├─ p001-img01.webp
         └─ p002-table01.webp
```

Markdown example:

```markdown
---
title: "sample"
source_file: "sample.pdf"
created: "2026-06-25"
type: "pdf-import"
---

# sample

<p align="center"><sub>PDF 1페이지</sub></p>

## Main heading

Paragraph text...

##### Table 1

| Item | Action |
| --- | --- |
| Example | Do this |

##### Image 1

![[Files/sample/p001-img01.webp]]
```

For `lecture.vtt`, the app creates a study note with overview, concepts, timeline sections, checklist, review questions, and Obsidian keyword links.

## Before / After Conversion Example

The project documentation uses only synthetic or redistributable examples. Private PDFs, paid course material, subtitle transcripts, and personal Obsidian notes must not be committed as examples.

Before:

```text
sample.pdf
├─ Page 1: title, paragraphs, and an embedded diagram
└─ Page 2: simple table and source link
```

After:

```text
output/
└─ sample/
   ├─ sample.md
   └─ Files/
      └─ sample/
         ├─ p001-img01.webp
         └─ p002-table01.webp
```

The generated Markdown keeps small PDF page markers, searchable text, Markdown tables when possible, Obsidian wiki image links, and a conversion report.

## PDF Conversion Profile

PDF conversion uses one profile: `manage-pdf-in-obsidian`.

This profile keeps PDFs lightweight and editable in Obsidian. It does not insert full-page `page_001.webp` images by default. It extracts the text layer first, restores headings, paragraphs, lists, Markdown tables, links, and necessary images, then stores PDF assets under `Files/<PDF title>/`.

When PyMuPDF can detect a simple table structure, PDF2Obsidian writes it as a Markdown table. Irregular tables can be saved as table-region WebP fallbacks instead of being forced into broken Markdown.

## PDF Compression

In `PDF/Image conversion` mode, choose `WebP Compression` from `Output` to create:

```text
output/
└─ sample/
   ├─ sample-compressed.pdf
   └─ sample-compression-report.md
```

This compression mode rasterizes each page, applies lossy WebP-based compression, and rebuilds a smaller PDF. It is separate from Markdown conversion and may not preserve selectable text, links, outlines, annotations, or form fields.

## Windows Notes

- If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

- If PySide6 fails to install, upgrade pip first:

```powershell
python -m pip install --upgrade pip
```

## OCR Notes

OCR is optional. The app still works without OCR libraries.

EasyOCR can be installed manually:

```powershell
pip install easyocr
```

Tesseract fallback requires the Tesseract application plus Python wrapper:

```powershell
pip install pytesseract
```

Install Tesseract for Windows separately from the official project or a trusted package manager. If OCR is enabled but no OCR engine is available, the app writes a clear message instead of crashing.

## Build EXE

Install dependencies, then run:

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

The build script uses:

```powershell
pyinstaller --noconfirm --windowed --name PDF2Obsidian src/pdf2obsidian/main.py
```

PySide6 sometimes needs extra hidden imports or resource collection depending on the local environment. If the EXE opens with missing Qt plugin errors, rebuild after upgrading PyInstaller and PySide6.

## Development

Run tests:

```powershell
pytest
```

Run lint:

```powershell
ruff check .
```

## How Codex Support Will Be Used

Codex support would be used to improve open-source maintenance work, not to make external AI APIs a required runtime dependency. Planned uses include:

- Improve PDF conversion quality across real-world documents.
- Add regression tests for PDF text extraction, embedded images, tables, and transcripts.
- Automate Windows build verification.
- Review pull requests for privacy, local-first behavior, and maintainability.
- Check for accidental hardcoded private file names, local paths, or sample documents.
- Improve documentation for non-developer Obsidian users.

## Roadmap

- Build toward a local-first study assistant experience.
- Improve OCR quality.
- Extract tables.
- Optimize output image dimensions.
- Add Markdown template settings.
- Add local web app mode.
- Add optional local LLM support only for better lecture-note reconstruction.
- Automate release builds.

## Future Web App Direction

The conversion logic lives under `src/pdf2obsidian/core/` so it can be reused from GUI, CLI, or FastAPI later.

The first web version should run locally on `localhost` and keep files on the user's PC. A hosted web version can be considered later with explicit privacy guidance and zip download support.

## GitHub Upload

Replace `<github-username>` with your GitHub username or use GitHub CLI:

```powershell
git init
git add .
git commit -m "Initial commit: PDF2Obsidian MVP"
git branch -M main
git remote add origin https://github.com/<github-username>/pdf2obsidian.git
git push -u origin main
```

With GitHub CLI:

```powershell
gh auth login
gh repo create pdf2obsidian --public --source=. --remote=origin --push
```

## Contributing

Issues and pull requests are welcome. Keep the project local-first, simple, and beginner-friendly. Do not add required cloud uploads, login, payments, or external AI API dependencies.

## License

MIT License. See [LICENSE](LICENSE).
