# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all data files
datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('requirements.txt', '.'),
]

# Hidden imports for Flask and extensions
hiddenimports = [
    'flask',
    'flask_sqlalchemy',
    'flask_login',
    'flask_wtf',
    'wtforms',
    'wtforms.csrf',
    'wtforms.fields',
    'wtforms.validators',
    'pymysql',
    'cryptography',
    'reportlab',
    'reportlab.lib',
    'reportlab.platypus',
    'reportlab.lib.styles',
    'reportlab.lib.pagesizes',
    'reportlab.lib.units',
    'reportlab.pdfgen',
    'openpyxl',
    'pandas',
    'PIL',
    'PIL._tkinter_finder',
    'python_dateutil',
    'dateutil',
    'dateutil.parser',
    'dateutil.relativedelta',
    'email_validator',
    'bcrypt',
    'dotenv',
]

# Binary files
binaries = []

# Analysis
a = Analysis(
    ['run.py'],
    pathex=[os.path.dirname(__file__)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# Add package data
for package in ['flask', 'werkzeug', 'jinja2', 'markupsafe', 'click', 'itsdangerous']:
    a.datas += collect_data_files(package)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TheophilePOS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False to hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'
)

# Create one-file executable
app = BUNDLE(
    exe,
    name='TheophilePOS.exe',
    icon='icon.ico',
    version='1.0.0',
    company_name='Theophile POS',
    file_description='Theophile POS Desktop Application',
    internal_name='TheophilePOS',
    legal_copyright='Copyright 2024',
    product_name='Theophile POS',
)