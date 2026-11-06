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
