@echo off
setlocal
cd /d "%~dp0"
title Gerar YT-DLP TUI.exe

call INICIAR_YT-DLP-TUI.bat --prepare-only >nul 2>&1
if errorlevel 1 goto :err

if not exist ".venv\Scripts\python.exe" (
  echo [ERRO] Ambiente Python nao encontrado. Execute INICIAR_YT-DLP-TUI.bat primeiro.
  pause
  exit /b 1
)

rem Reaplica a metadata e os pins desta release antes do build.
".venv\Scripts\python.exe" -m pip install -e .
if errorlevel 1 goto :err

".venv\Scripts\python.exe" -m pip install -U pyinstaller
if errorlevel 1 goto :err

".venv\Scripts\python.exe" -m pytest -q
if errorlevel 1 goto :err

".venv\Scripts\python.exe" -m compileall -q yt_dlp_tui
if errorlevel 1 goto :err

".venv\Scripts\python.exe" -m PyInstaller --clean --noconfirm yt-dlp-tui.spec
if errorlevel 1 goto :err

if exist "dist\yt-dlp-tui.exe" (
  echo.
  echo PRONTO: %CD%\dist\yt-dlp-tui.exe
  echo Deno ainda precisa estar instalado no Windows.
  echo.
  pause
  exit /b 0
)

echo [ERRO] O EXE nao foi encontrado em dist\.
pause
exit /b 1

:err
echo.
echo [ERRO] Falha ao preparar, testar ou gerar o EXE.
pause
exit /b 1
