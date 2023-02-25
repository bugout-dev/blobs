"""
Blockchain configurations
"""

from typing import Dict

from pydantic import BaseModel, parse_file_as, parse_raw_as
from web3 import Web3


class BlockchainDefinition(BaseModel):
    http: str
    chain_id: int
    expected_block_interval: float  # expected number of seconds between subsequent blocks


def load_definitions_from_file(filepath: str) -> Dict[str, BlockchainDefinition]:
    return parse_file_as(Dict[str, BlockchainDefinition], filepath)


def load_definitions_from_string(
    definitions_string: str,
) -> Dict[str, BlockchainDefinition]:
    return parse_raw_as(Dict[str, BlockchainDefinition], definitions_string)
