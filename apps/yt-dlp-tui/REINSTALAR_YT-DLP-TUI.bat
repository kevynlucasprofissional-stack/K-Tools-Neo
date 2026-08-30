@echo off
setlocal
cd /d "%~dp0"
if exist ".venv" rmdir /s /q ".venv"
echo Ambiente local removido. Execute INICIAR_YT-DLP-TUI.bat novamente.
pause
