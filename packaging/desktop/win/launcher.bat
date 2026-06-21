@echo off
setlocal
set CONFIG=%APPDATA%\c4reqber\config.toml
set TUI=%~dp0c4tui-v9.exe

if not exist "%CONFIG%" (
  echo First run — creating config...
  blast init
)

if not exist "%TUI%" (
  echo TUI binary missing: %TUI%
  exit /b 1
)

"%TUI%" %*