param(
    [string]$WallpaperPath = ""
)

$ErrorActionPreference = "Stop"
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Run .\setup.ps1 before launching CuteMica."
}

$arguments = @("-m", "cutemica.demo.main")
if ($WallpaperPath) {
    $arguments += @("--wallpaper", $WallpaperPath)
}

& $python @arguments
if ($LASTEXITCODE -ne 0) {
    throw "CuteMica exited with code $LASTEXITCODE."
}
