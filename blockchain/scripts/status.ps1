# SENTRA Hyperledger Fabric Windows Status Wrapper
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$NetworkDir = Join-Path $ScriptDir "..\network"

docker compose -f (Join-Path $NetworkDir "docker-compose-test-net.yaml") ps
