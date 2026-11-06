<#
.SYNOPSIS
  Build desktop EXE for LMS Assistant with PyInstaller

.DESCRIPTION
  Run from project root:
    .\scripts\build_exe.ps1
    .\scripts\build_exe.ps1 -Clean

  Output: dist\LMSAssistant\LMSAssistant.exe
#>

param(
    [switch]$Clean,
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "==> Project root: $Root" -ForegroundColor Cyan

# --- always write a known-good spec (avoids sync lag + old broken specs) ---
$PackDir = Join-Path $Root "packaging"
$Spec = Join-Path $PackDir "lms_assistant.spec"
if (-not (Test-Path $PackDir)) {
    New-Item -ItemType Directory -Path $PackDir | Out-Null
}

Write-Host "==> Writing packaging/lms_assistant.spec" -ForegroundColor Cyan
$specBody = @'
# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None
ROOT = Path(SPECPATH).resolve().parent

datas = []
binaries = []
assets_dir = ROOT / "assets"
if assets_dir.exists():
    datas.append((str(assets_dir), "assets"))
schema = ROOT / "src" / "storage" / "schema.sql"
if schema.exists():
    datas.append((str(schema), "src/storage"))
try:
    datas += collect_data_files("matplotlib")
except Exception:
    pass

hiddenimports = [
    "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets",
    "PySide6.QtNetwork", "PySide6.QtSvg",
    "matplotlib", "matplotlib.backends.backend_qtagg",
    "jdatetime", "loguru", "httpx", "bs4", "lxml",
    "cryptography", "dotenv",
]

# collect_all -> (datas, binaries, hiddenimports)
for pkg in ("PySide6", "matplotlib"):
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hidden
    except Exception:
        pass

hiddenimports = [h for h in hiddenimports if isinstance(h, str)]

a = Analysis(
    [str(ROOT / "scripts" / "run_gui.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["src.web", "uvicorn", "fastapi", "pytest", "matplotlib.tests"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
_icon = ROOT / "assets" / "icons" / "app.ico"
_ver = ROOT / "packaging" / "version_info.txt"
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="LMSAssistant",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(_icon) if _icon.exists() else None,
    version=str(_ver) if _ver.exists() else None,
)
coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=True, upx_exclude=[],
    name="LMSAssistant",
)
'@
Set-Content -Path $Spec -Value $specBody -Encoding UTF8

# --- venv ---
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
    Write-Host "WARNING: .venv not found - using system python" -ForegroundColor Yellow
}

# --- deps ---
Write-Host "==> Checking PyInstaller..." -ForegroundColor Cyan
& $Python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "==> Installing PyInstaller..." -ForegroundColor Cyan
    & $Python -m pip install -U pyinstaller
}

# --- clean ---
if ($Clean) {
    Write-Host "==> Cleaning build/ and dist/" -ForegroundColor Cyan
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $Root "build")
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $Root "dist")
}

# --- assets check ---
$Icon = Join-Path $Root "assets\icons\app.ico"
if (-not (Test-Path $Icon)) {
    Write-Host "WARNING: app.ico missing - continuing without icon resource" -ForegroundColor Yellow
}

Write-Host '==> Building onedir bundle with PyInstaller...' -ForegroundColor Cyan
& $Python -m PyInstaller $Spec --noconfirm
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit $LASTEXITCODE"
}

$Exe = Join-Path $Root "dist\LMSAssistant\LMSAssistant.exe"
if (Test-Path $Exe) {
    $size = [math]::Round((Get-Item $Exe).Length / 1MB, 2)
    Write-Host ""
    Write-Host "OK Build succeeded" -ForegroundColor Green
    Write-Host "   EXE: $Exe"
    Write-Host "   Size: ~$size MB (ship the whole dist\LMSAssistant folder)"
    Write-Host ""
    Write-Host "Next optional step: compile packaging\installer.iss with Inno Setup" -ForegroundColor Cyan
} else {
    throw "EXE was not created - check dist output"
}
