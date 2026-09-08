# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for building Flower as a desktop app.
# Build:  pyinstaller flower.spec
# Output: dist/Flower  (macOS: Flower.app, Windows: Flower.exe)

import sys

block_cipher = None

a = Analysis(
    ['flower.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('03-HeLA WT-C1.fcs', '.'),
        ('03-HeLa pMLM049 clone 6 Dark-B4.fcs', '.'),
        ('03-HeLa pMLM049 clone 6 Light-B3.fcs', '.'),
    ],
    hiddenimports=[
        'matplotlib.backends.backend_agg',
        'readfcs',
        'openpyxl',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'IPython', 'jupyter', 'notebook',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Flower',
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Flower',
)

# On macOS, wrap in a .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Flower.app',
        icon=None,
        bundle_identifier='com.flower.cytometry',
        info_plist={
            'CFBundleDisplayName': 'Flower',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.13',
        },
    )
