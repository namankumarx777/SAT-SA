# SENTRA Hyperledger Fabric Windows Shutdown Wrapper
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$NetworkDir = Join-Path $ScriptDir "..\network"

docker compose -f (Join-Path $NetworkDir "docker-compose-test-net.yaml") down -v --remove-orphans
Write-Host "SENTRA Fabric Network stopped." -ForegroundColor Yellow
