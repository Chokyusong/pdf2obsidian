# PDF2Obsidian Roadmap

This roadmap describes public project direction. For design rationale, see [Design decisions](decisions.md).

## Product Focus

PDF2Obsidian focuses on two outcomes:

1. Convert PDFs into Obsidian-ready Markdown and lightweight assets while preserving as much useful structure as practical.
2. Convert lecture subtitles into detailed study material that can be understood without watching the original video.

The project does not aim to become a general quiz, flashcard, mind map, or chatbot app. AI features must remain optional and user-controlled.

## Current Status

The current public release is `v0.1.5`.

Completed or available:

- Windows desktop GUI.
- PDF file selection and conversion.
- Image file selection and conversion.
- Drag and drop in the desktop GUI.
- PDF text extraction with PyMuPDF.
- Basic PDF structure restoration for headings, lists, paragraphs, and tables.
- Embedded PDF image extraction.
- Image compression to WebP.
- PDF to compressed raster PDF output mode.
- Optional local OCR wrapper.
- SRT, VTT, TXT, and Markdown transcript input.
- Structured transcript-to-study-note output.
- Optional Local AI mode with Ollama.
- Ollama status checks, model refresh, model pull, and user-confirmed installer workflow.
- GUI progress and log updates for PDF conversion, PDF compression, transcript conversion, and Ollama work.
- External prompt files packaged into Windows builds.
- Basic pytest and Ruff coverage.
- Windows PyInstaller build script.
- GitHub release ZIP asset.

## Next Release Goals

Near-term work should focus on reliability, verification, and user trust:

- Add automated workflow tests for the three main conversion paths:
  - subtitle to Markdown
  - PDF to Markdown plus images
  - PDF to compressed WebP PDF
- Add a release privacy scan for private paths, paid material titles, raw transcripts, API keys, and generated output folders.
- Add GitHub Actions release build research or automation.
- Improve README screenshots with only safe public sample files.
- Improve GUI status messages for long Ollama generations.
- Add clearer warnings when local AI output is saved with quality issues.
- Document model recommendations and expected performance more clearly.

## PDF Conversion Improvements

- Improve layout fidelity for multi-column PDFs.
- Improve table extraction and fallback behavior for irregular tables.
- Add regression tests for PDF headings, lists, tables, embedded images, and blank-image filtering.
- Add image size controls.
- Add Markdown template settings.
- Add better conversion error reporting per file.

## Lecture Transcript Improvements

- Improve subtitle line merging into readable paragraphs.
- Improve semantic section detection for introductions, definitions, examples, summaries, missions, checklists, and review questions.
- Improve Korean keyword extraction so meaningless frequent words are not treated as core concepts.
- Add more tests for prompt-leak cleanup, language heading rules, examples, action steps, cautions, and review questions.
- Keep prompts general and avoid course-specific hardcoding.

## AI Roadmap

Default conversion must continue to work without cloud AI.

Possible future work:

- Optional high-quality retry mode for Ollama users who accept slower generation.
- Optional OpenAI-compatible cloud AI mode as an explicit enhancement.
- Clear separation between Basic, Local AI, and future Cloud AI modes.
- Better local model guidance for normal PCs versus high-memory systems.

## Later

- CLI entry point for batch conversion.
- YouTube subtitle import workflow.
- Optional zip export.
- Local web app prototype with FastAPI or Streamlit.
- DOCX and PPTX research.
- Audio or video transcript workflow research.
- Signed Windows installer research.

## Open Source Maintenance Goals

- Keep issues organized with labels for PDF, image, OCR, transcript, GUI, docs, and tests.
- Publish release notes for every tagged version.
- Add beginner-friendly contribution tasks.
- Keep privacy and local-first constraints visible in documentation.
- Track public maintenance tasks in [maintenance.md](maintenance.md) before creating GitHub Issues.
- Run a privacy hardcoding scan before releases.
- Update [Design decisions](decisions.md) when project direction changes.
