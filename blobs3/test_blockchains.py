import os
import tempfile
import unittest

from . import blockchains


class TestLoadDefinitions(unittest.TestCase):
    def test_load_definitions_from_string(self):
        definitions_string = """
{
  "ethereum": {
    "chain_id": 1,
    "http": "http://example.com/ethereum",
    "expected_block_interval": 15
  },
  "polygon": {
    "chain_id": 137,
    "http": "https://polygon-rpc.com",
    "expected_block_interval": 2.3
  }
}
        """

        definitions = blockchains.load_definitions_from_string(definitions_string)
        expected_definitions = {
            "ethereum": blockchains.BlockchainDefinition(
                chain_id=1,
                http="http://example.com/ethereum",
                expected_block_interval=15.0,
            ),
            "polygon": blockchains.BlockchainDefinition(
                chain_id=137,
                http="https://polygon-rpc.com",
                expected_block_interval=2.3,
            ),
        }

        self.assertDictEqual(definitions, expected_definitions)

    def test_load_definitions_from_file(self):
        definitions_string = """
{
  "ethereum": {
    "chain_id": 1,
    "http": "http://example.com/ethereum",
    "expected_block_interval": 15
  },
  "polygon": {
    "chain_id": 137,
    "http": "https://polygon-rpc.com",
    "expected_block_interval": 2.3
  }
}
        """

        try:
            definitions_file = tempfile.mktemp()
            with open(definitions_file, "w") as ofp:
                ofp.write(definitions_string)

            definitions = blockchains.load_definitions_from_file(definitions_file)
            expected_definitions = {
                "ethereum": blockchains.BlockchainDefinition(
                    chain_id=1,
                    http="http://example.com/ethereum",
                    expected_block_interval=15.0,
                ),
                "polygon": blockchains.BlockchainDefinition(
                    chain_id=137,
                    http="https://polygon-rpc.com",
                    expected_block_interval=2.3,
                ),
            }
            self.assertDictEqual(definitions, expected_definitions)
        finally:
            os.remove(definitions_file)


if __name__ == "__main__":
    unittest.main()
