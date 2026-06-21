@echo off
setlocal
set CONFIG=%USERPROFILE%\.c4reqber\config.toml
set TUI=%~dp0c4tui-v9.exe

if not exist "%CONFIG%" (
  echo First run — creating config...
  blast init
)

REM Export key settings from config.toml for full-featured desktop app (OPENROUTER + DEEPSEEK + search keys + LEAN)
if exist "%CONFIG%" (
  for /f "tokens=2 delims==" %%a in ('findstr /r "^api_url" "%CONFIG%"') do set C4_API_URL=%%a
  for /f "tokens=2 delims==" %%a in ('findstr /r "^openrouter_api_key" "%CONFIG%"') do set OPENROUTER_API_KEY=%%a
  for /f "tokens=2 delims==" %%a in ('findstr /r "^deepseek_api_key" "%CONFIG%"') do set DEEPSEEK_API_KEY=%%a
  for /f "tokens=2 delims==" %%a in ('findstr /r "^brave_api_key" "%CONFIG%"') do set BRAVE_API_KEY=%%a
  for /f "tokens=2 delims==" %%a in ('findstr /r "^tavily_api_key" "%CONFIG%"') do set TAVILY_API_KEY=%%a
  for /f "tokens=2 delims==" %%a in ('findstr /r "^exa_api_key" "%CONFIG%"') do set EXA_API_KEY=%%a
  for /f "tokens=2 delims==" %%a in ('findstr /r "^xai_api_key" "%CONFIG%"') do set XAI_API_KEY=%%a
  for /f "tokens=2 delims==" %%a in ('findstr /r "^lean4_path" "%CONFIG%"') do set LEAN4_PATH=%%a
)

if not exist "%TUI%" (
  echo TUI binary missing: %TUI%
  exit /b 1
)

"%TUI%" %*