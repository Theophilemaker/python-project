@echo off
echo Building Theophile POS Desktop Application...
echo.

REM Install PyInstaller if not already installed
pip install pyinstaller

REM Build the application
pyinstaller theophile-pos.spec

echo.
echo Build complete! Check the dist/ folder.
pause