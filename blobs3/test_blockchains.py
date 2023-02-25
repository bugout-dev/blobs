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
    "poa": false,
    "http": "http://example.com/ethereum",
    "healthy_block_interval": 45
  },
  "polygon": {
    "chain_id": 137,
    "poa": true,
    "http": "https://polygon-rpc.com",
    "healthy_block_interval": 7.5
  }
}
        """

        cls.definitions_file = tempfile.mktemp()
        with open(cls.definitions_file, "w") as ofp:
            ofp.write(cls.definitions_string)

        cls.expected_definitions = {
            "ethereum": blockchains.BlockchainDefinition(
                chain_id=1,
                poa=False,
                http="http://example.com/ethereum",
                healthy_block_interval=45.0,
            ),
            "polygon": blockchains.BlockchainDefinition(
                chain_id=137,
                poa=True,
                http="https://polygon-rpc.com",
                healthy_block_interval=7.5,
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
