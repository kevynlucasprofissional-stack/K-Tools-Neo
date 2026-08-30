@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
    py removedor_sibilancia_gui.py
) else (
    python removedor_sibilancia_gui.py
)
if errorlevel 1 pause
