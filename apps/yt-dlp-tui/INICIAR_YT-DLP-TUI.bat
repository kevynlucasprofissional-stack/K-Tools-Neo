@echo off
setlocal
cd /d "%~dp0"
title YT-DLP TUI

set "PY_CMD=py -3"
%PY_CMD% --version >nul 2>&1
if errorlevel 1 set "PY_CMD=python"

%PY_CMD% --version >nul 2>&1
if errorlevel 1 (
  echo.
  echo [ERRO] Python nao foi encontrado.
  echo Instale Python 3.10 ou mais recente e tente novamente.
  echo.
  pause
  exit /b 1
)

%PY_CMD% -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 (
  echo.
  echo [ERRO] E necessario Python 3.10 ou mais recente.
  echo.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Preparando YT-DLP TUI na primeira execucao...
  %PY_CMD% -m venv .venv
  if errorlevel 1 goto :install_error
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  if errorlevel 1 goto :install_error
  ".venv\Scripts\python.exe" -m pip install -e .
  if errorlevel 1 goto :install_error
  echo.
)

".venv\Scripts\python.exe" -c "import yt_dlp, yt_dlp_ejs, imageio_ffmpeg, yt_dlp_tui" >nul 2>&1
if errorlevel 1 (
  echo Reparando dependencias...
  ".venv\Scripts\python.exe" -m pip install -e .
  if errorlevel 1 goto :install_error
)

if /I "%~1"=="--prepare-only" exit /b 0

".venv\Scripts\python.exe" -m yt_dlp_tui
exit /b %errorlevel%

:install_error
echo.
echo [ERRO] Nao foi possivel instalar as dependencias.
echo Verifique sua conexao com a internet e execute este arquivo novamente.
echo.
pause
exit /b 1
