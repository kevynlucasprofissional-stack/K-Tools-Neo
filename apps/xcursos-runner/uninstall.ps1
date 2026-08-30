param([switch]$KeepProfile)
$root=Join-Path $env:LOCALAPPDATA 'XCursosRunner'
$bin=Join-Path $root 'bin'
$userPath=[Environment]::GetEnvironmentVariable('Path','User')
if($userPath){
  $parts=@($userPath -split ';' | Where-Object { $_ -and ($_ -ne $bin) })
  [Environment]::SetEnvironmentVariable('Path',($parts -join ';'),'User')
}
if($KeepProfile){
  Remove-Item -Recurse -Force (Join-Path $root 'app') -ErrorAction SilentlyContinue
  Remove-Item -Recurse -Force $bin -ErrorAction SilentlyContinue
  Write-Host "Aplicacao removida; perfil/config preservados em $root"
}else{
  Remove-Item -Recurse -Force $root -ErrorAction SilentlyContinue
  Write-Host 'XCursos Runner removido.'
}
