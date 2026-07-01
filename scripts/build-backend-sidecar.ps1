param(
    [string]$TargetTriple = "",
    [switch]$SkipDependencyInstall
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$requirements = Join-Path $repoRoot "backend\requirements.txt"
$backendEntry = Join-Path $repoRoot "backend\main.py"
$distDir = Join-Path $repoRoot "frontend\src-tauri\binaries"
$workDir = Join-Path $repoRoot "build\pyinstaller\work"
$specDir = Join-Path $repoRoot "build\pyinstaller\spec"
$backendPath = Join-Path $repoRoot "backend"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating Python virtual environment at .venv"
    python -m venv (Join-Path $repoRoot ".venv")
}

if (-not $TargetTriple) {
    $TargetTriple = (& rustc --print host-tuple).Trim()
    if (-not $TargetTriple) {
        throw "Could not determine Rust target triple. Is rustc installed?"
    }
}

if (-not $SkipDependencyInstall) {
    Write-Host "Installing backend dependencies and PyInstaller into .venv"
    uv pip install --python $venvPython -r $requirements
    uv pip install --python $venvPython pyinstaller
}

New-Item -ItemType Directory -Force -Path $distDir, $workDir, $specDir | Out-Null

$binaryBaseName = "zeus-backend-$TargetTriple"
$existing = Join-Path $distDir "$binaryBaseName.exe"
if (Test-Path $existing) {
    Remove-Item -LiteralPath $existing -Force
}

Write-Host "Building Tauri sidecar: $binaryBaseName"
& $venvPython -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name $binaryBaseName `
    --paths $backendPath `
    --distpath $distDir `
    --workpath $workDir `
    --specpath $specDir `
    $backendEntry

if (-not (Test-Path $existing)) {
    throw "Expected sidecar binary was not created: $existing"
}

Write-Host "Sidecar ready: $existing"
