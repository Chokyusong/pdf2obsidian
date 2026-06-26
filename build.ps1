$ErrorActionPreference = "Stop"

$pythonCandidates = @(
    "python",
    "py",
    "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
)

$python = $null
foreach ($candidate in $pythonCandidates) {
    try {
        $command = Get-Command $candidate -ErrorAction Stop
        & $command.Source --version *> $null
        if ($LASTEXITCODE -eq 0) {
            $python = $command.Source
            break
        }
    } catch {
        if (Test-Path -LiteralPath $candidate) {
            & $candidate --version *> $null
            if ($LASTEXITCODE -eq 0) {
                $python = $candidate
                break
            }
        }
    }
}

if (-not $python) {
    throw "Python was not found. Install Python 3.11+ or activate a virtual environment first."
}

$promptData = Join-Path $PSScriptRoot "src\pdf2obsidian\prompts"

& $python -m PyInstaller `
    --noconfirm `
    --windowed `
    --name PDF2Obsidian `
    --add-data "$promptData;pdf2obsidian\prompts" `
    --exclude-module pandas `
    --exclude-module pyarrow `
    --exclude-module openpyxl `
    --exclude-module IPython `
    --exclude-module notebook `
    --exclude-module jupyter `
    --exclude-module pytest `
    --exclude-module tkinter `
    --exclude-module matplotlib `
    --exclude-module scipy `
    src/pdf2obsidian/main.py

Write-Host "Build complete. Check the dist/PDF2Obsidian folder."
