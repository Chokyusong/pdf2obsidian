# Contributing

Thank you for considering a contribution to PDF2Obsidian.

## Project Principles

- Keep the app local-first.
- Do not add required cloud uploads.
- Do not add required external AI APIs.
- Keep the MVP simple and reliable.
- Prefer clear documentation and tests over hidden behavior.

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

## Pull Request Checklist

- Tests pass.
- Ruff passes.
- README or docs are updated when behavior changes.
- No generated `output/`, `.venv/`, build artifacts, or private notes are committed.
