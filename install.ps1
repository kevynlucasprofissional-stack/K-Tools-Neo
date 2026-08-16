param([switch]$NoPathUpdate)
$ErrorActionPreference='Stop'
function Step($m){Write-Host "[XCursos V4.2.4] $m" -ForegroundColor Cyan}
function Warn($m){Write-Host "[AVISO] $m" -ForegroundColor Yellow}

$node=Get-Command node -ErrorAction SilentlyContinue
$npm=Get-Command npm -ErrorAction SilentlyContinue
if(-not $node -or -not $npm){throw 'Node.js/npm nao encontrados. Instale Node.js 24 LTS e execute novamente.'}
$major=[int]((& node -p "process.versions.node.split('.')[0]").Trim())
if($major -lt 22 -or $major -ge 27){throw "Node.js $major nao suportado. Use Node 22.x, 24.x ou 26.x; 24 LTS e recomendado."}

$chromeCandidates=@(
  (Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'),
  $(if(${env:ProgramFiles(x86)}){Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe'}),
  (Join-Path $env:LOCALAPPDATA 'Google\Chrome\Application\chrome.exe')
) | Where-Object { $_ -and (Test-Path $_) }
if(-not $chromeCandidates -and -not $env:XCURSOS_CHROME_PATH -and -not $env:CHROME_PATH){Warn 'Google Chrome Stable nao foi localizado nos caminhos padrao. Configure depois com: xcursos config --chrome "C:\caminho\chrome.exe"'}

$root=Join-Path $env:LOCALAPPDATA 'XCursosRunner'
$app=Join-Path $root 'app'
$bin=Join-Path $root 'bin'
$stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
$stage=Join-Path $root ".install-$stamp"
$backup=Join-Path $root "app.backup-$stamp"
New-Item -ItemType Directory -Force -Path $stage,$bin | Out-Null

Step 'Preparando instalacao em staging...'
Copy-Item -Recurse -Force (Join-Path $PSScriptRoot 'src') $stage
Copy-Item -Force (Join-Path $PSScriptRoot 'package.json') $stage
Copy-Item -Force (Join-Path $PSScriptRoot 'download-all.ps1') $stage

Push-Location $stage
try{
  Step 'Instalando playwright-core (sem Chromium empacotado)...'
  & npm install --omit=dev
  if($LASTEXITCODE -ne 0){throw 'npm install falhou.'}
  Step 'Verificando Playwright CDP runtime...'
  & node -e "import('playwright-core').then(({chromium})=>{if(!chromium || !chromium.connectOverCDP) process.exit(2); console.log('connectOverCDP OK')})"
  if($LASTEXITCODE -ne 0){throw 'Verificacao playwright-core falhou.'}
  & node --check src/cli.mjs
  if($LASTEXITCODE -ne 0){throw 'Verificacao sintatica da CLI falhou.'}
} finally { Pop-Location }

Step 'Ativando nova versao...'
try{
  if(Test-Path $app){Move-Item $app $backup}
  Move-Item $stage $app
} catch {
  if(Test-Path $app){Remove-Item -Recurse -Force $app -ErrorAction SilentlyContinue}
  if(Test-Path $backup){Move-Item $backup $app -ErrorAction SilentlyContinue}
  throw
}

$cmd=Join-Path $bin 'xcursos.cmd'
@"
@echo off
node "$app\src\cli.mjs" %*
"@ | Set-Content -Encoding ASCII $cmd

$allCmd=Join-Path $bin 'xcursos-all.cmd'
@"
@echo off
powershell -ExecutionPolicy Bypass -File "$app\download-all.ps1" %*
"@ | Set-Content -Encoding ASCII $allCmd

if(-not $NoPathUpdate){
  $userPath=[Environment]::GetEnvironmentVariable('Path','User')
  $parts=@($userPath -split ';' | Where-Object { $_ })
  if($parts -notcontains $bin){$newPath=(@($parts)+$bin) -join ';';[Environment]::SetEnvironmentVariable('Path',$newPath,'User');$env:Path="$env:Path;$bin"}
}

Step 'Instalacao concluida.'
Write-Host "Comando: $cmd"
Write-Host "Curso inteiro com retry seguro: $allCmd"
Write-Host 'Fluxo recomendado: xcursos doctor -> xcursos login -> xcursos probe --json'
if(-not (Get-Command yt-dlp -ErrorAction SilentlyContinue)){Warn 'yt-dlp nao foi encontrado no PATH. Instale-o antes de baixar videos ou defina YTDLP_PATH.'}
if(-not (Get-Command ffprobe -ErrorAction SilentlyContinue)){Warn 'ffprobe nao foi encontrado no PATH. Instale FFmpeg/ffprobe antes de baixar videos ou defina FFPROBE_PATH.'}
