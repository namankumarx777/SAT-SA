#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NETWORK_DIR="${SCRIPT_DIR}/../network"

echo "Stopping SENTRA Hyperledger Fabric containers..."
docker compose -f "${NETWORK_DIR}/docker-compose-test-net.yaml" down -v --remove-orphans
echo "SENTRA Fabric network stopped."
