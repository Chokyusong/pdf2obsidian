# Development Log

## 2026-06-25

Initial MVP scaffold.

- Created Python package structure under `src/pdf2obsidian`.
- Added PySide6 GUI entry point.
- Added PDF conversion with PyMuPDF.
- Added image conversion with Pillow.
- Added optional OCR wrapper for EasyOCR and Tesseract.
- Added transcript parsing and learning-note generation.
- Added Obsidian Markdown writers.
- Added pytest tests.
- Added PyInstaller build script.
- Added GitHub Actions workflow.

## GitHub Upload Commands

If GitHub CLI is installed and authenticated:

```powershell
gh auth status
gh repo create pdf2obsidian --public --source=. --remote=origin --push
```

Manual Git flow:

```powershell
git init
git add .
git commit -m "Initial commit: PDF2Obsidian MVP"
git branch -M main
git remote add origin https://github.com/<github-username>/pdf2obsidian.git
git push -u origin main
```

Replace `<github-username>` with your GitHub username.

## Repository Checklist

- README completed.
- MIT LICENSE included.
- CHANGELOG included.
- Repository guidance is kept concise and public-safe.
- requirements.txt completed.
- pyproject.toml completed.
- pytest should pass before push.
- Ruff should pass before push.
- output folder excluded.
- .venv folder excluded.
- __pycache__ excluded.
- No API keys or credentials included.
