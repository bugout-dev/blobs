import os
import tempfile
import unittest

from . import blockchains


class TestLoadDefinitions(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.definitions_string = """
{
  "ethereum": {
    "chain_id": 1,
    "http": "http://example.com/ethereum",
    "expected_block_interval": 15,
    "healthcheck_blocks": 3
  },
  "polygon": {
    "chain_id": 137,
    "http": "https://polygon-rpc.com",
    "expected_block_interval": 2.3,
    "healthcheck_blocks": 20
  }
}
        """

        cls.definitions_file = tempfile.mktemp()
        with open(cls.definitions_file, "w") as ofp:
            ofp.write(cls.definitions_string)

        cls.expected_definitions = {
            "ethereum": blockchains.BlockchainDefinition(
                chain_id=1,
                http="http://example.com/ethereum",
                expected_block_interval=15.0,
                healthcheck_blocks=3,
            ),
            "polygon": blockchains.BlockchainDefinition(
                chain_id=137,
                http="https://polygon-rpc.com",
                expected_block_interval=2.3,
                healthcheck_blocks=20,
            ),
        }

        return super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        os.remove(cls.definitions_file)
        return super().tearDownClass()

    def test_load_definitions_from_string(self):
        definitions = blockchains.load_definitions_from_string(self.definitions_string)
        self.assertDictEqual(definitions, self.expected_definitions)

    def test_load_definitions_from_file(self):
        definitions = blockchains.load_definitions_from_file(self.definitions_file)
        self.assertDictEqual(definitions, self.expected_definitions)


if __name__ == "__main__":
    unittest.main()
