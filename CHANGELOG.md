# Changelog

## Unreleased

## 0.1.5 - 2026-06-27

### Added

- Added timestamps to GUI log messages.
- Added prompt-leak cleanup for Ollama output before saving Markdown.
- Added tests for prompt-leak cleanup, wiki-link cleanup, thinking-trace cleanup, and v1.1 heading rules.

### Changed

- Changed default Local AI(Ollama) transcript conversion to a one-shot flow with light post-processing instead of slow repeated quality retry and section fallback reconstruction.
- Increased default Ollama transcript chunk size so typical lecture transcripts can be handled in one request.
- Kept `qwen2.5:7b` as the recommended practical Ollama model and documented `qwen3.6` as a large experimental model.
- Updated Ollama documentation to explain that local execution is free after installation, but speed and quality depend on the model and PC hardware.
- Updated release links to v0.1.5.

### Fixed

- Fixed leaked prompt headings such as `PRIMARY GOAL`, `OUTPUT LANGUAGE`, and `FIXED MARKDOWN STRUCTURE` appearing before the actual lecture note.
- Fixed generated Obsidian wiki links and thinking/reasoning traces being retained in final Ollama Markdown.

## 0.1.4 - 2026-06-27

### Changed

- Replaced the Ollama lecture reconstruction prompt with a universal Korean/English prompt.
- Removed course-specific hardcoded lecture preservation checks and forced content insertion.
- Updated Local AI documentation for the optional bilingual transcript-to-Obsidian workflow.

### Fixed

- Fixed Windows CLI decoding for Ollama and winget checks so Korean output does not crash latest-version checks.

## 0.1.3 - 2026-06-26

### Added

- Fixed lecture study note template documentation.
- AI Mode design for Basic, optional Local AI with Ollama, and future Cloud AI.
- Output Mode structure for Review Note, Lecture Reconstruction MD, Ebook, and Executive Brief.
- Optional Ollama client and mock-tested AI reconstruction foundation.
- External prompt files for lecture and output-mode guidance.
- Beginner-friendly Ollama setup guide in the app and documentation.
- Local AI transcript output now stores Ollama's final Markdown directly instead of wrapping it again.
- Output Language option for transcript notes: same as source, Korean, or English.
- Strengthened Local AI prompt to preserve source information and generate lecture reconstruction Markdown instead of a shortened note.
- Added creator information to the license, package metadata, README files, GUI footer, and CLI version output.
- Ollama installer and model download progress in the GUI status area, log, and progress bar.
- Real-time conversion progress for PDF pages, PDF compression pages, transcript stages, and Ollama reconstruction chunks.

### Changed

- GUI now opens in a wider two-row dashboard layout with Input, Conversion, and AI settings on the first row.
- Run status and log are shown on the second row, with the log visible by default.

## 0.1.2 - 2026-06-26

### Added

- PDF compression output mode with compression report.
- Windows `test.cmd` launcher for GUI and check workflows.
- Open-source positioning, safe example, contribution, and security documentation for Codex support preparation.

### Changed

- PDF conversion now prefers text-layer extraction and embedded image export.
- PDF pages are no longer rendered as WebP images by default.
- Lecture transcript conversion now produces structured study notes from cleaned transcript content.
- README and examples now describe the project as a local-first tool for Obsidian users and learning-material managers.

### Fixed

- Blank or low-information PDF images are skipped during extraction.
- Detached PDF bullet markers are merged with the following text line.
- PDF compression savings are shown in GUI logs.

## 0.1.1 - 2026-06-25

### Added

- README badges and GUI screenshot.
- Example output documentation.
- Contributing and security policy documents.
- Privacy guidance for safe sample files and local-first contribution rules.

## 0.1.0 - 2026-06-25

### Added

- Initial PDF2Obsidian MVP.
- PDF to Obsidian Markdown conversion.
- PDF page rendering to WebP assets.
- Image to WebP conversion.
- Optional local OCR wrapper.
- Lecture transcript to learning-note conversion.
- Minimal PySide6 GUI.
- PyInstaller build script.
- pytest and Ruff configuration.
