@echo off
echo ========================================
echo    Theophile POS - Complete Build Tool
echo ========================================
echo.

:MENU
echo Choose build option:
echo.
echo [1] Build Electron Desktop App
echo [2] Build PyInstaller Executable
echo [3] Build Tkinter Desktop App
echo [4] Create Windows Installer
echo [5] Build Docker Container
echo [6] Build ALL
echo [7] Exit
echo.

set /p choice="Enter choice (1-7): "

if "%choice%"=="1" goto electron
if "%choice%"=="2" goto pyinstaller
if "%choice%"=="3" goto tkinter
if "%choice%"=="4" goto installer
if "%choice%"=="5" goto docker
if "%choice%"=="6" goto all
if "%choice%"=="7" goto exit

:electron
echo.
echo Building Electron Desktop App...
cd theophile-pos-desktop
call npm install
call npm run build:win
cd ..
echo Electron build complete!
goto menu

:pyinstaller
echo.
echo Building PyInstaller Executable...
call pip install pyinstaller
call pyinstaller theophile-pos.spec
echo PyInstaller build complete!
goto menu

:tkinter
echo.
echo Building Tkinter Desktop App...
echo No build needed - just run tkinter_app.py
goto menu

:installer
echo.
echo Creating Windows Installer...
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
    echo Installer created in installer\ folder!
) else (
    echo Inno Setup not found!
    echo Please download from: https://jrsoftware.org/isdl.php
)
goto menu

:docker
echo.
echo Building Docker Container...
docker-compose build
echo Docker build complete!
goto menu

:all
echo.
echo Building ALL packages...
call :electron
call :pyinstaller
call :installer
call :docker
echo All builds complete!
goto menu

:exit
echo.
echo Build process completed!
pause