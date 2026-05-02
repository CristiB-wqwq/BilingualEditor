# -*- mode: python ; coding: utf-8 -*-
import os, importlib

# Locate customtkinter package directory for theme data files
ctk_path = os.path.dirname(importlib.import_module("customtkinter").__file__)

a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('Template.pro', '.'),
        ('GroupNames.txt', '.'),
        (ctk_path, 'customtkinter'),
    ],
    hiddenimports=['customtkinter', 'darkdetect'],
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
    name='BilingualEditor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
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
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BilingualEditor',
)

app = BUNDLE(
    coll,
    name='BilingualEditor.app',
    icon=None,
    bundle_identifier=None,
)
