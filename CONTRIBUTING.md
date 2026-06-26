# Contributing

Thank you for considering a contribution to PDF2Obsidian.

## Project Principles

- Keep the app local-first.
- Do not add required cloud uploads.
- Do not add required external AI APIs.
- Keep the MVP simple and reliable.
- Prefer clear documentation and tests over hidden behavior.
- Keep public examples safe: do not commit personal PDFs, paid course material, subtitle transcripts, or private Obsidian notes.
- Check [Design decisions](docs/decisions.md) before changing project direction.
- Check [Roadmap](docs/roadmap.md) before adding new large features.

## Development Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run checks:

```powershell
pytest
ruff check .
```

## Good First Contributions

- Improve Windows installation docs.
- Add example PDF/image/transcript outputs.
- Improve OCR setup guidance.
- Add tests for transcript parsing.
- Improve error messages in the GUI.

## Safe Sample Data

Sample files must be public, synthetic, or explicitly redistributable. Do not include:

- Personal PDFs or private documents.
- Paid course material or copyrighted learning resources.
- Raw subtitle transcripts from private or paid lectures.
- Personal Obsidian vault notes or local vault paths.
- Real API keys, credentials, or private URLs.

When in doubt, create a tiny synthetic PDF, image, or transcript directly inside a test.

## Pull Request Checklist

- Tests pass.
- Ruff passes.
- README or docs are updated when behavior changes.
- Tests and docs are updated when conversion behavior changes.
- `docs/decisions.md` is updated when a design decision changes.
- Privacy check is complete: no private file names, local paths, paid material titles, transcripts, or personal notes are included.
- No generated `output/`, `.venv/`, build artifacts, or private notes are committed.
