$ErrorActionPreference = "Stop"

$localAppData = [Environment]::GetFolderPath("LocalApplicationData")
if (-not $localAppData) {
    $localAppData = $env:LOCALAPPDATA
}
$localPython = Join-Path $localAppData "Programs\Python\Python312\python.exe"
$pythonCandidates = @()
$pythonCandidates += $localPython

foreach ($pythonRoot in @($env:pythonLocation, $env:Python_ROOT_DIR, $env:Python3_ROOT_DIR)) {
    if ($pythonRoot) {
        $pythonCandidates += (Join-Path $pythonRoot "python.exe")
    }
}

if ($env:USERPROFILE) {
    $pythonCandidates += (Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe")
}

$pythonCandidates += "python"
$pythonCandidates += "py"

$python = $null
foreach ($candidate in $pythonCandidates) {
    if (-not $candidate) {
        continue
    }
    try {
        $source = $null
        if (Test-Path -LiteralPath $candidate) {
            $source = $candidate
        } else {
            $command = Get-Command $candidate -ErrorAction Stop
            $source = $command.Source
        }
        & $source --version *> $null
        if ($LASTEXITCODE -eq 0) {
            $python = $source
            break
        }
    } catch {
        continue
    }
}

if (-not $python) {
    throw "Python was not found. Install Python 3.11+ or activate a virtual environment first."
}

Write-Host "Using Python: $python"

$promptData = Join-Path $PSScriptRoot "src\pdf2obsidian\prompts"

$pyInstallerArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--windowed",
    "--name", "PDF2Obsidian",
    "--add-data", "$promptData;pdf2obsidian\prompts",
    "--exclude-module", "pandas",
    "--exclude-module", "pyarrow",
    "--exclude-module", "openpyxl",
    "--exclude-module", "IPython",
    "--exclude-module", "notebook",
    "--exclude-module", "jupyter",
    "--exclude-module", "pytest",
    "--exclude-module", "tkinter",
    "--exclude-module", "matplotlib",
    "--exclude-module", "scipy",
    "src/pdf2obsidian/main.py"
)

function ConvertTo-ProcessArgument {
    param([Parameter(Mandatory = $true)][string]$Argument)

    if ($Argument -notmatch '[\s"]') {
        return $Argument
    }

    return '"' + ($Argument -replace '"', '\"') + '"'
}

$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $python
$startInfo.Arguments = ($pyInstallerArgs | ForEach-Object { ConvertTo-ProcessArgument $_ }) -join " "
$startInfo.WorkingDirectory = $PSScriptRoot
$startInfo.UseShellExecute = $false

$process = [System.Diagnostics.Process]::Start($startInfo)
$process.WaitForExit()
if ($process.ExitCode -ne 0) {
    throw "PyInstaller failed with exit code $($process.ExitCode)"
}

Write-Host "Build complete. Check the dist/PDF2Obsidian folder."
