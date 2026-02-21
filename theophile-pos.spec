# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('config.py', '.'),
        ('models.py', '.'),
        ('forms.py', '.'),
        ('decorators.py', '.'),
        ('utils.py', '.'),
        ('company_helper.py', '.'),
    ],
    hiddenimports=[
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'flask_wtf',
        'wtforms',
        'pymysql',
        'cryptography',
        'reportlab',
        'openpyxl',
        'pandas',
        'PIL',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

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

# Create a one-file bundle
app = BUNDLE(
    exe,
    name='TheophilePOS.app',
    icon='icon.icns',
    bundle_identifier='com.theophile.pos',
)