; Inno Setup script for C4REQBER Windows installer
;
; Kept in sync with the canonical Go TUI version
; (src/tui/v9/cmd/c4tui-v9/main.go: `var version = "v9.13.0"`).
; When the Go side bumps, update here AND packaging/desktop/mac/Info.plist
; AND packaging/desktop/c4reqber-desktop.spec (3 places, see CHANGELOG).
#define MyAppName "C4REQBER"
#define MyAppVersion "9.13.0"
#define MyAppPublisher "c4reqber"
#define MyAppURL "https://c4reqber.org"
#define MyAppCopyright "(c) 2026 c4reqber - GitLab cognitive-functors/turbo-cdi"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppCopyright={#MyAppCopyright}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=C4REQBER-setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
; Native installer runs as 64-bit. The bundled Go TUI binary
; (c4tui-v9-windows-amd64.exe or -arm64.exe) is selected by the
; build_all target in src/tui/v9/Makefile. Both arch bundles ship
; to {app} via the [Files] section; the launcher.bat picks the
; right one at runtime via %PROCESSOR_ARCHITECTURE%.
ArchitecturesInstallIn64BitMode=x64compatible
; min Windows 10 (matches lipgloss + Go 1.21 runtime requirements)
MinVersion=10.0

[Files]
Source: "..\..\..\dist\C4REQBER\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
; Audit 2026-06-22 H-2: ship BOTH x86_64 and arm64 TUI binaries.
; launcher.bat picks the right one based on %PROCESSOR_ARCHITECTURE%.
Source: "c4tui-v9.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "c4tui-v9-arm64.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "launcher.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\launcher.bat"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\launcher.bat"

[Run]
Filename: "{app}\launcher.bat"; Description: "Launch {#MyAppName}"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\c4reqber"