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
        "token_id": "var/tokenId",
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
        self.assertEqual(storage_access.authorization.token_id, "var/tokenId")
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


class TestMatchPaths(unittest.TestCase):
    def test_match_simple(self):
        authorization = access.AuthorizationSpecification(
            blockchain="wyrm",
            authorization_type=access.AuthorizationType.ERC1155,
            contract_address="0x49ca1f6801c085abb165a827badfd6742a3f8dbc",
            token_id=1,
            minimum_balance=1,
        )
        storage_access = access.StorageAccess(
            storage_path=["bucket-name", "good-dir", "good-subdir"],
            authorization=authorization,
            access=access.AccessType.CREATE,
        )

        path_components = [
            "bucket-name",
            "good-dir",
            "good-subdir",
            "something-else",
            "image.png",
        ]

        is_match, variable_bindings = access.match_paths(
            access.AccessType.CREATE, path_components, storage_access
        )

        self.assertTrue(is_match)
        self.assertDictEqual(variable_bindings, {})

    def test_match_with_variables(self):
        authorization = access.AuthorizationSpecification(
            blockchain="wyrm",
            authorization_type=access.AuthorizationType.ERC721,
            contract_address="0xDfbC5320704b417C5DBbd950738A32B8B5Ed75b3",
            token_id="var/tokenId",
            minimum_balance=1,
        )
        storage_access = access.StorageAccess(
            storage_path=["bucket-name", "good-dir", "good-subdir", "var/tokenId"],
            authorization=authorization,
            access=access.AccessType.CREATE,
        )

        path_components = [
            "bucket-name",
            "good-dir",
            "good-subdir",
            "42",
            "image.png",
        ]

        is_match, variable_bindings = access.match_paths(
            access.AccessType.CREATE, path_components, storage_access
        )

        self.assertTrue(is_match)
        self.assertDictEqual(variable_bindings, {"var/tokenId": "42"})

    def test_nonmatch_simple(self):
        authorization = access.AuthorizationSpecification(
            blockchain="wyrm",
            authorization_type=access.AuthorizationType.ERC1155,
            contract_address="0x49ca1f6801c085abb165a827badfd6742a3f8dbc",
            token_id=1,
            minimum_balance=1,
        )
        storage_access = access.StorageAccess(
            storage_path=["bucket-name", "good-dir", "good-subdir"],
            authorization=authorization,
            access=access.AccessType.CREATE,
        )

        path_components = [
            "bucket-name",
            "good-dir",
            "bad-subdir",
            "image.png",
        ]

        is_match, variable_bindings = access.match_paths(
            access.AccessType.CREATE, path_components, storage_access
        )

        self.assertFalse(is_match)
        self.assertDictEqual(variable_bindings, {})

    def test_nonmatch_with_variables(self):
        authorization = access.AuthorizationSpecification(
            blockchain="wyrm",
            authorization_type=access.AuthorizationType.ERC721,
            contract_address="0xDfbC5320704b417C5DBbd950738A32B8B5Ed75b3",
            token_id="var/tokenId",
            minimum_balance=1,
        )
        storage_access = access.StorageAccess(
            storage_path=[
                "bucket-name",
                "good-dir",
                "good-subdir",
                "var/tokenId",
                "another-subdir",
            ],
            authorization=authorization,
            access=access.AccessType.CREATE,
        )

        path_components = [
            "bucket-name",
            "good-dir",
            "good-subdir",
            "42",
            "image.png",
        ]

        is_match, variable_bindings = access.match_paths(
            access.AccessType.CREATE, path_components, storage_access
        )

        self.assertFalse(is_match)
        self.assertDictEqual(variable_bindings, {})


if __name__ == "__main__":
    unittest.main()
