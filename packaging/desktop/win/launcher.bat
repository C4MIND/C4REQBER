@echo off
setlocal EnableExtensions EnableDelayedExpansion
set CONFIG=%USERPROFILE%\.c4reqber\config.toml

REM Audit 2026-06-22 H-2: select correct TUI binary for current architecture.
REM %PROCESSOR_ARCHITECTURE% is "AMD64" on x86_64 and "ARM64" on Windows on ARM.
REM The Makefile builds both binaries; the installer ships both. Without this
REM branch, Windows-on-ARM users run the x86_64 binary under emulation.
if /i "%PROCESSOR_ARCHITECTURE%"=="ARM64" (
  set TUI=%~dp0c4tui-v9-arm64.exe
) else (
  set TUI=%~dp0c4tui-v9.exe
)
set BLAST=%~dp0blast.exe

REM First-run guard: create the central config if missing.
REM Use the bundled blast.exe (same dir as this launcher), not a PATH
REM lookup — installers don't always extend %PATH% for the user.
if not exist "%CONFIG%" (
  echo First run ^— creating config...
  if exist "%BLAST%" (
    "%BLAST%" init
  ) else (
    echo WARNING: blast.exe not found at %BLAST% — skipping config init.
    echo          (TUI v9 will still launch; wizard will run on first start.)
  )
)

REM Export from ~/.c4reqber/config.toml for full desktop (central keys:
REM OPENROUTER/DEEPSEEK/TAVILY/EXA etc). The TOML writer always produces
REM one key per line, so findstr /b matches the line regardless of which
REM [section] header it lives under.
if exist "%CONFIG%" (
  for /f "usebackq tokens=2 delims==" %%a in (`findstr /b /c:"api_url" "%CONFIG%"`) do set C4_API_URL=%%a
  for /f "usebackq tokens=2 delims==" %%a in (`findstr /b /c:"language" "%CONFIG%"`) do set C4_LANG=%%a
  for /f "usebackq tokens=2 delims==" %%a in (`findstr /b /c:"email" "%CONFIG%"`) do set C4_API_EMAIL=%%a
  for /f "usebackq tokens=2 delims==" %%a in (`findstr /b /c:"password" "%CONFIG%"`) do set C4_API_PASSWORD=%%a
  for /f "usebackq tokens=2 delims==" %%a in (`findstr /b /c:"openrouter_api_key" "%CONFIG%"`) do set OPENROUTER_API_KEY=%%a
  for /f "usebackq tokens=2 delims==" %%a in (`findstr /b /c:"deepseek_api_key" "%CONFIG%"`) do set DEEPSEEK_API_KEY=%%a
  for /f "usebackq tokens=2 delims==" %%a in (`findstr /b /c:"brave_api_key" "%CONFIG%"`) do set BRAVE_API_KEY=%%a
  for /f "usebackq tokens=2 delims==" %%a in (`findstr /b /c:"tavily_api_key" "%CONFIG%"`) do set TAVILY_API_KEY=%%a
  for /f "usebackq tokens=2 delims==" %%a in (`findstr /b /c:"exa_api_key" "%CONFIG%"`) do set EXA_API_KEY=%%a
  for /f "usebackq tokens=2 delims==" %%a in (`findstr /b /c:"xai_api_key" "%CONFIG%"`) do set XAI_API_KEY=%%a
  for /f "usebackq tokens=2 delims==" %%a in (`findstr /b /c:"lean4_path" "%CONFIG%"`) do set LEAN4_PATH=%%a
  REM Strip the quotes the toml writer adds (e.g. "foo" ^-^> foo). Safe
  REM even when values contain '=' (base64 padding in API keys) because
  REM tokens=2 + delims== only splits on the FIRST '='.
  for %%V in (C4_API_URL C4_LANG C4_API_EMAIL C4_API_PASSWORD OPENROUTER_API_KEY DEEPSEEK_API_KEY BRAVE_API_KEY TAVILY_API_KEY EXA_API_KEY XAI_API_KEY LEAN4_PATH) do (
    if defined %%V set %%V=!%%V:"=!
  )
)

if not exist "%TUI%" (
  echo TUI binary missing: %TUI%
  exit /b 1
)

REM Desktop splash header (port of terminal splash). Mirrors the mac
REM launcher so both desktop launchers brand the same.
echo C4REQBER DESKTOP  ·  Creative ^& Destructive Insights · At Your Fingertips
echo Discover.  Invent.  Shift paradigms.
echo GitLab · c4reqber · Z3^3
echo.

REM Launch TUI v9 (the rich Python splash from launcher_entry is shown
REM when launched through the .app on macOS; on Windows users go
REM straight into the Go TUI which has its own animated splash).
"%TUI%" %*
