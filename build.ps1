$ErrorActionPreference = "Stop"

python -m PyInstaller --noconfirm --windowed --name PDF2Obsidian src/pdf2obsidian/main.py

Write-Host "Build complete. Check the dist/PDF2Obsidian folder."
