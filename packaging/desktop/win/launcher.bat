@echo off
setlocal
set CONFIG=%USERPROFILE%\.c4reqber\config.toml
set TUI=%~dp0c4tui-v9.exe

if not exist "%CONFIG%" (
  echo First run — creating config...
  blast init
)

REM Export from ~/.c4reqber/config.toml for full desktop (central keys: OPENROUTER/DEEPSEEK/TAVILY/EXA etc)
if exist "%CONFIG%" (
  for /f "tokens=2 delims==" %%a in ('findstr /r "^api_url" "%CONFIG%"') do set C4_API_URL=%%a
  for /f "tokens=2 delims==" %%a in ('findstr /r "^openrouter_api_key" "%CONFIG%"') do set OPENROUTER_API_KEY=%%a
  for /f "tokens=2 delims==" %%a in ('findstr /r "^deepseek_api_key" "%CONFIG%"') do set DEEPSEEK_API_KEY=%%a
  for /f "tokens=2 delims==" %%a in ('findstr /r "^brave_api_key" "%CONFIG%"') do set BRAVE_API_KEY=%%a
  for /f "tokens=2 delims==" %%a in ('findstr /r "^tavily_api_key" "%CONFIG%"') do set TAVILY_API_KEY=%%a
  for /f "tokens=2 delims==" %%a in ('findstr /r "^exa_api_key" "%CONFIG%"') do set EXA_API_KEY=%%a
  for /f "tokens=2 delims==" %%a in ('findstr /r "^xai_api_key" "%CONFIG%"') do set XAI_API_KEY=%%a
  for /f "tokens=2 delims==" %%a in ('findstr /r "^lean4_path" "%CONFIG%"') do set LEAN4_PATH=%%a
  REM Strip quotes that toml writer adds (e.g. "foo" -> foo). Simple post clean for cmd.
  if defined C4_API_URL set C4_API_URL=%C4_API_URL:"=%
  if defined OPENROUTER_API_KEY set OPENROUTER_API_KEY=%OPENROUTER_API_KEY:"=%
  if defined DEEPSEEK_API_KEY set DEEPSEEK_API_KEY=%DEEPSEEK_API_KEY:"=%
  if defined BRAVE_API_KEY set BRAVE_API_KEY=%BRAVE_API_KEY:"=%
  if defined TAVILY_API_KEY set TAVILY_API_KEY=%TAVILY_API_KEY:"=%
  if defined EXA_API_KEY set EXA_API_KEY=%EXA_API_KEY:"=%
  if defined XAI_API_KEY set XAI_API_KEY=%XAI_API_KEY:"=%
  if defined LEAN4_PATH set LEAN4_PATH=%LEAN4_PATH:"=%
)

if not exist "%TUI%" (
  echo TUI binary missing: %TUI%
  exit /b 1
)

"%TUI%" %*