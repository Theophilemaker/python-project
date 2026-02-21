; Theophile POS Installer Script
[Setup]
AppName=Theophile POS
AppVersion=1.0
AppPublisher=Theophile Systems
AppPublisherURL=https://theophile.com
AppSupportURL=https://theophile.com/support
DefaultDirName={pf}\TheophilePOS
DefaultGroupName=Theophile POS
UninstallDisplayIcon={app}\TheophilePOS.exe
Compression=lzma2
SolidCompression=yes
OutputDir=installer
OutputBaseFilename=TheophilePOS_Setup
SetupIconFile=icon.ico
WizardImageFile=logo.bmp
WizardSmallImageFile=smalllogo.bmp

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: checkablealone
Name: "quicklaunchicon"; Description: "Create a &Quick Launch shortcut"; GroupDescription: "Additional icons:"; Flags: checkablealone; OnlyBelowVersion: 0,6.1

[Files]
; Main application
Source: "dist\TheophilePOS\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

; Database
Source: "database.sql"; DestDir: "{app}\db"; Flags: ignoreversion

; Python runtime
Source: "python-3.11.0-embed-amd64\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\Theophile POS"; Filename: "{app}\TheophilePOS.exe"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"
Name: "{group}\Uninstall Theophile POS"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Theophile POS"; Filename: "{app}\TheophilePOS.exe"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\TheophilePOS.exe"; Description: "Launch Theophile POS"; Flags: postinstall nowait skipifsilent

[UninstallRun]
; Stop any running instances
Filename: "{app}\python\python.exe"; Parameters: "-c ""import os; os.system('taskkill /f /im TheophilePOS.exe')"""; Flags: runhidden