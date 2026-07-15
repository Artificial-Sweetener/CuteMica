$ErrorActionPreference = "Stop"

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    python -m venv (Join-Path $PSScriptRoot ".venv")
    if ($LASTEXITCODE -ne 0) { throw "Virtual environment creation failed." }
}

& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }
& $venvPython -m pip install -e "$PSScriptRoot[dev]"
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }
