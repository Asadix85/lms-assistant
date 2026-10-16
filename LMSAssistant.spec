# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['scripts/run_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('src/storage/schema.sql', 'src/storage')],
    hiddenimports=['keyring.backends.Windows', 'keyring.backends.SecretService', 'keyring.backends.kwallet', 'aiogram', 'jdatetime', 'matplotlib.backends.backend_qtagg'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LMSAssistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icons/app.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LMSAssistant',
)
