# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

# Add the src directory to Python path
src_path = os.path.abspath('src')
sys.path.insert(0, src_path)

block_cipher = None

a = Analysis(
    ['src/main.py'],  # Main entry point
    pathex=[src_path],  # Add src directory to path
    binaries=[],
    datas=[
        ('service-account.json', '.'),  # Include service account credentials
        ('.env', '.'),  # Include environment variables
        ('src/ui', 'src/ui'),  # Include UI module
        ('src/core', 'src/core'),  # Include core module
        ('src/utils', 'src/utils'),  # Include utils module
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'google.oauth2',
        'google.auth.transport.requests',
        'google_auth_oauthlib.flow',
        'googleapiclient.discovery',
        'googleapiclient.http',
        'googleapiclient.errors',
        'obswebsocket',
        'obswebsocket.requests',
        'obswebsocket.events',
        'python-dotenv',
        'dotenv',  # Add dotenv explicitly
        'src',  # Add src package
        'src.ui',  # Add ui package
        'src.core',  # Add core package
        'src.utils',  # Add utils package
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
    name='MathsByPawanSir',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False to hide console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
) 