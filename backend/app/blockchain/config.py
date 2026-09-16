from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BlockchainConfig:
    network_name: str = os.getenv("SATSA_FABRIC_NETWORK", "SENTRA-network")
    channel_name: str = os.getenv("SATSA_FABRIC_CHANNEL", "SENTRA-channel")
    chaincode_name: str = os.getenv("SATSA_FABRIC_CHAINCODE", "SENTRA-integrity")
    peer_endpoint: str = os.getenv("SATSA_FABRIC_PEER", "localhost:7051")
    msp_id: str = os.getenv("SATSA_FABRIC_MSPID", "SupervisorMSP")
    crypto_dir: Path = Path(os.getenv("SATSA_FABRIC_CRYPTO", "blockchain/network/crypto-material"))
    connection_profile: Path = Path(os.getenv("SATSA_FABRIC_PROFILE", "blockchain/network/connection-org1.json"))
    enable_gateway: bool = os.getenv("SATSA_FABRIC_ENABLED", "true").lower() in ("true", "1", "yes")


blockchain_config = BlockchainConfig()
