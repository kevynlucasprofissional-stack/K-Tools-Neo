@echo off
setlocal
title K-Tools Neo - Workflow Editor (xyflow)

:: Posicionar no diretorio raiz do projeto
cd /d "%~dp0"

echo ======================================================================
echo             K-TOOLS NEO - WORKFLOW CANVAS ^& NODE PACKS
echo ======================================================================
echo.

:: 1. Verificar se npm esta instalado
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] O comando 'npm' nao foi encontrado no seu sistema.
    echo.
    echo O K-Tools Neo novo utiliza o editor visual baseado em xyflow/React.
    echo Para executa-lo, instale o Node.js em: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

:: 2. Navegar para a pasta do editor xyflow
cd "spikes\xyflow-editor"

:: 3. Instalar dependencias caso seja a primeira execucao
if not exist "node_modules\" (
    echo [INFO] Primeira execucao detectada. Instalando dependencias do xyflow...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao instalar dependencias do npm.
        pause
        exit /b 1
    )
)

:: 4. Iniciar o editor e abrir automaticamente no navegador padrao
echo [INFO] Abrindo o K-Tools Neo com xyflow no navegador...
echo.
echo ======================================================================
echo  URL: http://localhost:5173
echo  Para fechar o software, pressione Ctrl+C ou feche esta janela.
echo ======================================================================
echo.

call npm run dev -- --open

if errorlevel 1 (
    echo.
    echo [INFO] Aplicacao encerrada.
    pause
)
