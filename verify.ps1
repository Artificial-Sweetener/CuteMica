$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$python = Join-Path $root ".venv\Scripts\python.exe"
$ruff = Join-Path $root ".venv\Scripts\ruff.exe"
$mypy = Join-Path $root ".venv\Scripts\mypy.exe"
$motionBenchmark = Join-Path $root ".venv\Scripts\cutemica-benchmark-motion.exe"
$widgetMotionBenchmark = Join-Path $root ".venv\Scripts\cutemica-benchmark-widget-motion.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Run .\setup.ps1 before verification."
}

Push-Location $root
$previousQtPlatform = $env:QT_QPA_PLATFORM
try {
    $env:QT_QPA_PLATFORM = "offscreen"
    & $ruff format --check .
    if ($LASTEXITCODE -ne 0) { throw "Ruff formatting check failed." }
    & $ruff check .
    if ($LASTEXITCODE -ne 0) { throw "Ruff lint failed." }
    & $mypy --strict src tests
    if ($LASTEXITCODE -ne 0) { throw "Strict mypy failed." }
    & $python -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw "Pytest failed." }
    & $motionBenchmark --frames 600 --p95-budget-ms 1.5
    if ($LASTEXITCODE -ne 0) { throw "Offscreen renderer benchmark failed." }
    & $widgetMotionBenchmark --frames 600 --p95-budget-ms 1.5
    if ($LASTEXITCODE -ne 0) { throw "Offscreen widget benchmark failed." }
    & $python -m cutemica.demo.main --wallpaper tests/assets/ci-wallpaper.ppm --smoke-test
    if ($LASTEXITCODE -ne 0) { throw "GUI smoke test failed." }
}
finally {
    if ($null -eq $previousQtPlatform) {
        Remove-Item Env:\QT_QPA_PLATFORM -ErrorAction SilentlyContinue
    }
    else {
        $env:QT_QPA_PLATFORM = $previousQtPlatform
    }
    Pop-Location
}
