@echo off
chcp 65001 >nul
title K-Tools Neo - Workflow Editor (xyflow)
cd /d "%~dp0"

echo ======================================================================
echo             K-TOOLS NEO - WORKFLOW CANVAS ^& NODE PACKS
echo ======================================================================
echo.
echo [1/3] Configurando ambiente Python e pacotes do monorepo...
set "PYTHONPATH=%~dp0packages\ktools-core\src;%~dp0packages\ktools-json\src;%~dp0packages\ktools-text\src;%~dp0packages\ktools-pdf\src;%~dp0packages\ktools-documents\src;%~dp0packages\ktools-images\src;%~dp0packages\ktools-filesystem\src;%~dp0packages\ktools-media\src;%PYTHONPATH%"

echo [2/3] Verificando ambiente Node.js / npm...
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] O comando 'npm' não foi encontrado no sistema.
    echo O K-Tools Neo com editor baseado em xyflow precisa do Node.js para rodar a interface.
    echo Por favor, instale o Node.js em: https://nodejs.org/ (versão LTS recomendada).
    echo.
    pause
    exit /b 1
)

cd /d "%~dp0spikes\xyflow-editor"

if not exist "node_modules\" (
    echo.
    echo [INFO] Primeira execução detectada. Instalando dependências do xyflow-editor...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao instalar dependências do npm.
        pause
        exit /b 1
    )
)

echo [3/3] Iniciando o K-Tools Neo com xyflow e abrindo no navegador...
echo.
echo ======================================================================
echo  Interface abrindo em: http://localhost:5173
echo  Para encerrar o software, basta fechar esta janela ou pressionar Ctrl+C
echo ======================================================================
echo.

call npm run dev -- --open

if errorlevel 1 (
    echo.
    echo [AVISO] O servidor foi encerrado.
    pause
)
