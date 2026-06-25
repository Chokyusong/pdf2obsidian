# Changelog

## Unreleased

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
