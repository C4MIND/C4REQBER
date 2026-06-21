; Inno Setup script for C4REQBER Windows installer
#define MyAppName "C4REQBER"
#define MyAppVersion "5.6.0"
#define MyAppPublisher "c4reqber"
#define MyAppURL "https://c4reqber.org"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=C4REQBER-setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "..\..\..\dist\C4REQBER\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "c4tui-v9.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\launcher.bat"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\launcher.bat"

[Run]
Filename: "{app}\launcher.bat"; Description: "Launch {#MyAppName}"; Flags: postinstall nowait skipifsilent