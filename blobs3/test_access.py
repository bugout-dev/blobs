import unittest

from pydantic import ValidationError

from . import access


class TestStorageAccess(unittest.TestCase):
    def test_simple_path_private_access(self):
        access_string = """
{
    "storage_path": ["bucket-name", "dir1", "dir2"],
    "authorization": {
        "blockchain": "wyrm",
        "authorization_type": "ERC1155",
        "contract_address": "0x49ca1f6801c085abb165a827badfd6742a3f8dbc",
        "token_id": "1",
        "minimum_balance": "1"
    },
    "access": "CREATE"
}
        """

        storage_access = access.StorageAccess.parse_raw(access_string)

        self.assertListEqual(
            storage_access.storage_path, ["bucket-name", "dir1", "dir2"]
        )
        self.assertEqual(storage_access.authorization.blockchain, "wyrm")
        self.assertEqual(
            storage_access.authorization.authorization_type,
            access.AuthorizationType.ERC1155.value,
        )
        self.assertEqual(
            storage_access.authorization.contract_address,
            "0x49ca1F6801c085ABB165a827baDFD6742a3f8DBc",
        )
        self.assertEqual(storage_access.authorization.token_id, 1)
        self.assertEqual(storage_access.authorization.minimum_balance, 1)
        self.assertEqual(storage_access.access, access.AccessType.CREATE.value)

    def test_variable_path_private_access(self):
        access_string = """
{
    "storage_path": ["bucket-name", "dir1", "var/tokenId"],
    "authorization": {
        "blockchain": "wyrm",
        "authorization_type": "ERC1155",
        "contract_address": "0x49ca1f6801c085abb165a827badfd6742a3f8dbc",
        "token_id": "1",
        "minimum_balance": "1"
    },
    "access": "CREATE"
}
        """

        storage_access = access.StorageAccess.parse_raw(access_string)

        self.assertListEqual(
            storage_access.storage_path, ["bucket-name", "dir1", "var/tokenId"]
        )
        self.assertEqual(storage_access.authorization.blockchain, "wyrm")
        self.assertEqual(
            storage_access.authorization.authorization_type,
            access.AuthorizationType.ERC1155.value,
        )
        self.assertEqual(
            storage_access.authorization.contract_address,
            "0x49ca1F6801c085ABB165a827baDFD6742a3f8DBc",
        )
        self.assertEqual(storage_access.authorization.token_id, 1)
        self.assertEqual(storage_access.authorization.minimum_balance, 1)
        self.assertEqual(storage_access.access, access.AccessType.CREATE.value)

    def test_invalid_path(self):
        access_string = """
{
    "storage_path": ["bucket-name", "dir1", "dir2/dir3"],
    "authorization": {
        "blockchain": "wyrm",
        "authorization_type": "ERC1155",
        "contract_address": "0x49ca1f6801c085abb165a827badfd6742a3f8dbc",
        "token_id": "1",
        "minimum_balance": "1"
    },
    "access": "CREATE"
}
        """

        with self.assertRaises(ValidationError):
            access.StorageAccess.parse_raw(access_string)


if __name__ == "__main__":
    unittest.main()
