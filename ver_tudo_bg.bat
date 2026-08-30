@echo off
setlocal

set "OUT=%USERPROFILE%\Desktop\diagnostico_bg"
if not exist "%OUT%" mkdir "%OUT%"

echo ============================================
echo Gerando diagnostico em: "%OUT%"
echo ============================================

echo [1/8] Processos em execucao...
tasklist /v > "%OUT%\01_processos_detalhados.txt"
tasklist /svc > "%OUT%\02_processos_com_servicos.txt"
tasklist /m > "%OUT%\03_processos_com_modulos.txt"

echo [2/8] Servicos (ativos e inativos)...
sc query state= all > "%OUT%\04_servicos_todos.txt"

echo [3/8] Drivers via Service Control...
sc query type= driver state= all > "%OUT%\05_drivers_sc.txt"

echo [4/8] Drivers instalados detalhados...
driverquery /v /fo csv > "%OUT%\06_drivers_detalhados.csv"

echo [5/8] Tarefas agendadas...
schtasks /query /fo LIST /v > "%OUT%\07_tarefas_agendadas.txt"

echo [6/8] Conexoes, portas, PID e executaveis...
netstat -abno > "%OUT%\08_netstat_abno.txt"

echo [7/8] Itens de inicializacao pelo Registro...
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" > "%OUT%\09_startup_hkcu_run.txt" 2>&1
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce" > "%OUT%\10_startup_hkcu_runonce.txt" 2>&1
reg query "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" > "%OUT%\11_startup_hklm_run.txt" 2>&1
reg query "HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce" > "%OUT%\12_startup_hklm_runonce.txt" 2>&1

echo [8/8] Informacoes gerais do sistema...
systeminfo > "%OUT%\13_systeminfo.txt"

echo.
echo Concluido.
echo Abra a pasta:
echo %OUT%
echo.
pause