# PDF2Obsidian Roadmap

## Product Focus

PDF2Obsidian focuses on two outcomes:

1. Convert PDFs into Obsidian Markdown without drifting away from the original visual layout.
2. Convert lecture or YouTube subtitles into detailed study material that can be understood without watching the original video.

The project does not aim to become a general quiz, flashcard, mind map, or chatbot app. Optional local AI may be considered later only if it improves lecture-note reconstruction while keeping the local-first workflow.

## 0.1.0 MVP

- PDF file selection and conversion.
- Image file selection and conversion.
- Drag and drop in the desktop GUI.
- PDF text extraction with PyMuPDF.
- PDF page rendering, text extraction, and embedded image export.
- Image compression to WebP.
- Optional local OCR wrapper.
- Obsidian Markdown output.
- Lecture transcript to study-note conversion.
- Basic pytest coverage.
- Windows PyInstaller build script.

## 0.2.0

- Add downloadable Windows release asset.
- Add more real-world sample outputs.
- Add transcript parsing tests.
- Improve PDF visual layout fidelity.
- Improve lecture subtitle cleanup and detailed reconstruction.
- Improve OCR setup documentation.
- Add image size controls.
- Add Markdown template settings.
- Add CLI entry point for batch conversion.
- Add better conversion error reporting per file.

## 0.3.0

- Table extraction research.
- Local web app prototype with FastAPI or Streamlit.
- Optional zip export.
- More transcript templates.
- YouTube subtitle import workflow.

## Later

- Optional local LLM integration only for lecture-note reconstruction.
- Automated release packaging.
- Signed Windows installer research.

## Open Source Maintenance Goals

- Keep issues organized with labels for PDF, image, OCR, transcript, GUI, docs, and tests.
- Publish small release notes for every tagged version.
- Add beginner-friendly contribution tasks.
- Keep privacy and local-first constraints visible in documentation.
