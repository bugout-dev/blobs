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
    expected_block_interval: float  # expected number of seconds between subsequent blocks
    healthcheck_blocks: int  # Frequency (in number of expected blocks) at which to run healthchecks


def load_definitions_from_file(filepath: str) -> Dict[str, BlockchainDefinition]:
    return parse_file_as(Dict[str, BlockchainDefinition], filepath)


def load_definitions_from_string(
    definitions_string: str,
) -> Dict[str, BlockchainDefinition]:
    return parse_raw_as(Dict[str, BlockchainDefinition], definitions_string)


@dataclass
class Blockchain:
    client: Web3
    http: str
    chain_id: int
    expected_block_interval: float
    healthcheck_blocks: int
    last_block_number: int
    last_block_timestamp: int
    healthy: bool


class BlockchainManager:
    def __init__(self, blockchain_definitions: Dict[str, BlockchainDefinition]):
        pass
