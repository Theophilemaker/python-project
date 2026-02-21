@echo off
title Theophile POS Installer
color 0A
echo ========================================
echo    Theophile POS Installation Wizard
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed!
    echo Downloading Python installer...
    powershell -Command "Invoke-WebRequest https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe -OutFile python-installer.exe"
    echo Installing Python...
    start /wait python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python-installer.exe
) else (
    echo [✓] Python is installed
)

REM Install required packages
echo Installing required packages...
pip install -r requirements.txt

REM Create desktop shortcut
echo Creating desktop shortcut...
set SCRIPT="%TEMP%\%RANDOM%-script.vbs"
(
    echo Set oWS = WScript.CreateObject("WScript.Shell"^)
    echo sLinkFile = oWS.SpecialFolders("Desktop"^) + "\Theophile POS.lnk"
    echo Set oLink = oWS.CreateShortcut(sLinkFile^)
    echo oLink.TargetPath = "%~dp0start_pos.bat"
    echo oLink.WorkingDirectory = "%~dp0"
    echo oLink.IconLocation = "%~dp0icon.ico"
    echo oLink.Description = "Theophile POS"
    echo oLink.Save
) > %SCRIPT%
cscript /nologo %SCRIPT%
del %SCRIPT%

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Theophile POS has been installed successfully!
echo.
echo To start the application, use the desktop shortcut
echo or run start_pos.bat
echo.
pause