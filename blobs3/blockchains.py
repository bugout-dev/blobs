"""
Blockchain configurations
"""

from dataclasses import dataclass
import threading
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, parse_file_as, parse_raw_as
from web3 import Web3
from web3.middleware.geth_poa import geth_poa_middleware


class BlockchainDefinition(BaseModel):
    """
    Blockchain configuration is expected to be JSON-formatted conforming to this structure.
    """

    http: str
    poa: bool
    chain_id: int
    healthy_block_interval: float  # number of seconds between subsequent blocks at which node is considered healthy


def load_definitions_from_file(filepath: str) -> Dict[str, BlockchainDefinition]:
    """
    Loads a list of blockchain definitions from a file.
    """
    return parse_file_as(Dict[str, BlockchainDefinition], filepath)


def load_definitions_from_string(
    definitions_string: str,
) -> Dict[str, BlockchainDefinition]:
    """
    Loads a list of blockchain definitions from a JSON string (or bytes).
    """
    return parse_raw_as(Dict[str, BlockchainDefinition], definitions_string)


class BlockchainHealth(BaseModel):
    """
    Represents the healthcheck status of a blockchain
    """

    http: str
    chain_id: int
    healthy_block_interval: float
    last_block_number: int
    last_block_timestamp: int
    healthy: bool


@dataclass
class Blockchain:
    """
    Internal representation of a blockchain, including a web3 client to the chain and healthchecks.
    """

    http: str
    chain_id: int
    healthy_block_interval: float
    client: Web3
    last_block_number: int
    last_block_timestamp: int
    healthy: bool
    lock: threading.Lock


def apply_healthcheck(blockchain: Blockchain) -> None:
    """
    Runs a healthcheck on the given blockchain and mutates it to reflect the results of the healthcheck.
    """
    acquired = blockchain.lock.acquire(True, timeout=1.0)

    if not acquired:
        blockchain.healthy = False
        return

    try:
        current_block = blockchain.client.eth.get_block("latest")
        if (
            current_block.number <= blockchain.last_block_number
            or current_block.timestamp <= blockchain.last_block_timestamp
        ):
            blockchain.healthy = False
        else:
            blockchain.healthy = True
        blockchain.last_block_number = current_block.number
        blockchain.last_block_timestamp = current_block.timestamp
    finally:
        blockchain.lock.release()


class RepeatingTimer(threading.Thread):
    """
    Adapted from: https://stackoverflow.com/a/47292806
    """

    def __init__(
        self,
        interval_seconds: float,
        callback: Callable,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__()
        self.stop_event = threading.Event()
        self.interval_seconds = interval_seconds
        self.callback = callback

        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        self.args = args
        self.kwargs = kwargs

    def run(self):
        while not self.stop_event.wait(self.interval_seconds):
            self.callback(*self.args, **self.kwargs)

    def stop(self):
        self.stop_event.set()


class BlockchainManager:
    """
    BlockchainManager maps the names of available blockchains to the data required to interact with them.

    Primarily, it contains a web3 client corresponding to each available blockchain and, if the healthchecks
    have been started, it also keeps a record of the health of each chain.

    healthchecks can be started using start_healthchecks. The health checks, if you are using them,
    check the latest block on the available node every healthy_block_interval seconds. If the block
    number has not increased since the last check, the node is marked as unhealthy. Else, it is marked
    as healthy.

    Once healthchecks have been started, you can stop them at any time using the stop_healthcheks method.
    Once healthchecks have stopped, they cannot be started again.
    """

    def __init__(self, blockchain_definitions: Dict[str, BlockchainDefinition]):
        self.blockchains: Dict[str, Blockchain] = {}
        self.timers: Dict[str, Optional[RepeatingTimer]] = {}
        for blockchain_name, blockchain_def in blockchain_definitions.items():
            assume_healthy = blockchain_def.healthy_block_interval <= 0
            blockchain = Blockchain(
                http=blockchain_def.http,
                chain_id=blockchain_def.chain_id,
                healthy_block_interval=blockchain_def.healthy_block_interval,
                client=Web3(Web3.HTTPProvider(blockchain_def.http)),
                last_block_number=0,
                last_block_timestamp=0,
                healthy=assume_healthy,
                lock=threading.Lock(),
            )
            # Important: Add poa middleware for Proof of Authority chains
            if blockchain_def.poa:
                blockchain.client.middleware_onion.inject(geth_poa_middleware, layer=0)
            self.blockchains[blockchain_name] = blockchain
            if assume_healthy:
                self.timers[blockchain_name] = None
            else:
                self.timers[blockchain_name] = RepeatingTimer(
                    blockchain.healthy_block_interval,
                    apply_healthcheck,
                    args=[blockchain],
                )

    def start_healthchecks(self):
        for blockchain in self.blockchains.values():
            apply_healthcheck(blockchain)
        for timer in self.timers.values():
            if timer is not None:
                timer.start()

    def stop_healthchecks(self):
        for blockchain_name, timer in self.timers.items():
            if timer is not None:
                timer.stop()
                self.blockchains[blockchain_name].healthy = False

    def health_status(self) -> Dict[str, BlockchainHealth]:
        status = {
            name: BlockchainHealth(
                http=blockchain.http,
                chain_id=blockchain.chain_id,
                healthy_block_interval=blockchain.healthy_block_interval,
                last_block_number=blockchain.last_block_number,
                last_block_timestamp=blockchain.last_block_timestamp,
                healthy=blockchain.healthy,
            )
            for name, blockchain in self.blockchains.items()
        }
        return status

    def get(self, blockchain_name: str) -> Optional[Blockchain]:
        return self.blockchains.get(blockchain_name)
