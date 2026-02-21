@echo off
echo Building Theophile POS Desktop Application...

REM Install dependencies
call npm install

REM Build for Windows
call npm run build:win

echo Build complete! Check the dist/ folder for your installer.
pause