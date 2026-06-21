@echo off
setlocal
set CONFIG=%USERPROFILE%\.c4reqber\config.toml
set TUI=%~dp0c4tui-v9.exe

if not exist "%CONFIG%" (
  echo First run — creating config...
  blast init
)

REM Export key settings from config.toml for full-featured desktop app
if exist "%CONFIG%" (
  for /f "tokens=2 delims==" %%a in ('findstr /r "^api_url" "%CONFIG%"') do set C4_API_URL=%%a
  for /f "tokens=2 delims==" %%a in ('findstr /r "^openrouter_api_key" "%CONFIG%"') do set OPENROUTER_API_KEY=%%a
  for /f "tokens=2 delims==" %%a in ('findstr /r "^deepseek_api_key" "%CONFIG%"') do set DEEPSEEK_API_KEY=%%a
)

if not exist "%TUI%" (
  echo TUI binary missing: %TUI%
  exit /b 1
)

"%TUI%" %*