# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('*.py', '.'),
        ('security/*.py', 'security'),
        ('ai_assistant/core/*.py', 'ai_assistant/core'),
        ('ai_assistant/providers/*.py', 'ai_assistant/providers'),
        ('data', 'data'),
    ],
    hiddenimports=[
        'PyQt5.QtWebEngineWidgets',
        'cryptography',
        'bcrypt',
        'keyring',
        'openai',
        'feedparser',
        'sqlalchemy',
        'email',
        'imaplib',
        'smtplib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='WestfallPersonalAssistant',
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
    icon='assets/icon.ico' if Path('assets/icon.ico').exists() else None,
)

app = BUNDLE(
    exe,
    name='WestfallPersonalAssistant.app',
    icon='assets/icon.icns' if Path('assets/icon.icns').exists() else None,
    bundle_identifier='com.westfallsoftwares.personalassistant',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'LSBackgroundOnly': 'False',
    },
)