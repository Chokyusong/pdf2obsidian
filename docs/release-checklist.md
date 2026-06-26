# Release Checklist

Use this checklist before publishing a GitHub release.

## Version

- Update `pyproject.toml`.
- Update `src/pdf2obsidian/__init__.py`.
- Update release links in `README.md`.
- Update release links in `README_ko.md`.
- Update `CHANGELOG.md`.

## Quality Checks

Run:

```powershell
ruff check .
pytest
```

For release candidates, also verify the main workflows with safe sample files:

- Subtitle to Markdown.
- PDF to Markdown plus images.
- PDF to compressed WebP PDF.

Do not use private files, paid course material, or personal Obsidian notes for public screenshots or release assets.

## Build

Build a fresh Windows package:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
```

Confirm the output contains:

- `dist/PDF2Obsidian/PDF2Obsidian.exe`
- `dist/PDF2Obsidian/_internal/pdf2obsidian/prompts/lecture_study_note_ko.txt`

Create the release ZIP from the fresh `dist/PDF2Obsidian` folder.

## Privacy Scan

Before committing or releasing, check that public files do not contain:

- Private local paths.
- Personal file names.
- Paid course titles.
- Raw private transcripts.
- API keys or organization IDs.
- Generated output folders.
- Build artifacts.

## GitHub Release

- Commit with a Conventional Commit message.
- Push `main`.
- Create and push the release tag.
- Create the GitHub Release.
- Upload the Windows ZIP asset.
- Verify the release page and asset name.

## Cleanup

Move generated local artifacts to `.trash/cleanup-YYYYMMDD-HHMMSS/` when cleanup is requested:

- `build/`
- `dist/`
- `*.spec`
- `.tmp/`
- cache folders

Keep `.trash/` ignored.
