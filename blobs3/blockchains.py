"""
Blockchain configurations
"""

from dataclasses import dataclass
from typing import Dict

from pydantic import BaseModel, parse_file_as, parse_raw_as
from web3 import Web3


class BlockchainDefinition(BaseModel):
    http: str
    chain_id: int
    healthy_block_interval: float  # number of seconds between subsequent blocks at which node is considered healthy


def load_definitions_from_file(filepath: str) -> Dict[str, BlockchainDefinition]:
    return parse_file_as(Dict[str, BlockchainDefinition], filepath)


def load_definitions_from_string(
    definitions_string: str,
) -> Dict[str, BlockchainDefinition]:
    return parse_raw_as(Dict[str, BlockchainDefinition], definitions_string)


@dataclass
class Blockchain:
    http: str
    chain_id: int
    healthy_block_interval: float
    client: Web3
    last_block_number: int
    last_block_timestamp: int
    healthy: bool


class BlockchainManager:
    def __init__(self, blockchain_definitions: Dict[str, BlockchainDefinition]):
        self.blockchains: Dict[str, Blockchain] = {}
        for blockchain_name, blockchain_def in blockchain_definitions.items():
            blockchain = Blockchain(
                http=blockchain_def.http,
                chain_id=blockchain_def.chain_id,
                healthy_block_interval=blockchain_def.healthy_block_interval,
                client=Web3(Web3.HTTPProvider(blockchain_def.http)),
                last_block_number=0,
                last_block_timestamp=0,
                healthy=False,
            )
            self.blockchains[blockchain_name] = blockchain

    # def start(self):
