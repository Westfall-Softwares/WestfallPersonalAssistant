# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Westfall Personal Assistant Backend

Creates a standalone backend binary that can be bundled with Electron.
"""

import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

block_cipher = None

# Determine data files to include
data_files = [
    ('westfall_backend/routers', 'westfall_backend/routers'),
    ('westfall_backend/services', 'westfall_backend/services'),
]

# Hidden imports (modules that PyInstaller might miss)
hidden_imports = [
    'backend.westfall_backend.app',
    'backend.westfall_backend.routers.health',
    'backend.westfall_backend.routers.llm', 
    'backend.westfall_backend.routers.tools',
    'backend.westfall_backend.services.settings',
    'backend.westfall_backend.services.logging',
    'backend.westfall_backend.services.llama_supervisor',
    'uvicorn',
    'uvicorn.main',
    'uvicorn.server',
    'fastapi',
    'pydantic',
    'pydantic_settings',
    'llama_cpp',
]

a = Analysis(
    ['westfall_backend/app.py'],
    pathex=[project_root],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='westfall-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='backend/version_info.txt',  # Optional: version info for Windows
)

# Create distribution directory structure
dist_dir = Path('dist-backend')
if sys.platform == 'win32':
    platform_dir = dist_dir / 'win'
elif sys.platform == 'darwin':
    platform_dir = dist_dir / 'mac'
else:
    platform_dir = dist_dir / 'linux'

# Copy the executable to the platform-specific directory
import shutil
platform_dir.mkdir(parents=True, exist_ok=True)