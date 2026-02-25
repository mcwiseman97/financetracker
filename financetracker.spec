# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Finance Tracker.
Bundles QSS themes and default categories alongside the executable.
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Theme stylesheets
        ('app/ui/themes/dark.qss',  'app/ui/themes'),
        ('app/ui/themes/light.qss', 'app/ui/themes'),
        # Bootstrap categories for first run
        ('data/default_categories.json', 'data'),
    ],
    hiddenimports=[
        'dateutil',
        'dateutil.relativedelta',
        'babel',
        'babel.numbers',
        'matplotlib',
        'matplotlib.backends.backend_qtagg',
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
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
    a.datas,
    [],
    name='financetracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # no terminal window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
