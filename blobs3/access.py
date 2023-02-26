"""
Access control layer for blobs3
"""

from enum import Enum
from typing import cast, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, parse_file_as, parse_raw_as, validator
from web3 import Web3

from .blockchains import BlockchainManager
from .contracts.ERC20_interface import Contract as ERC20
from .contracts.ERC721_interface import Contract as ERC721
from .contracts.ERC1155_interface import Contract as ERC1155


class AuthorizationType(str, Enum):
    PUBLIC = "PUBLIC"
    ERC20 = "ERC20"
    ERC721 = "ERC721"
    ERC1155 = "ERC1155"


class AccessType(str, Enum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"


class AuthorizationSpecification(BaseModel):
    """
    Specifies a token-based authorization condition.
    """

    blockchain: str
    authorization_type: AuthorizationType
    contract_address: Optional[str] = None
    token_id: Optional[Union[int, str]] = None
    minimum_balance: Optional[int] = None

    @validator("contract_address")
    def contract_address_must_be_convertible_to_checksum_address(cls, v):
        try:
            checksum_address = Web3.toChecksumAddress(v)
        except Exception:
            raise ValueError(
                "contract_address could not be converted to checksum address"
            )
        return checksum_address

    class Config:
        use_enum_values = True


class StorageAccess(BaseModel):
    """
    Primitive representation of an access authorization to a storage path.
    """

    storage_path: List[str]
    authorization: AuthorizationSpecification
    access: AccessType

    @validator("storage_path")
    def validate_storage_path(cls, v: List[str]):
        for component in v:
            if "/" in component and not (
                component.startswith("var/") and len(component.split("/")) == 2
            ):
                raise ValueError(
                    f'Invalid storage_path component: {component}. If components contain a /, they should be of the form "var/<varname>" where <varname> has no /.'
                )
        return v

    class Config:
        use_enum_values = True


def load_access_list_from_file(filepath: str):
    """
    Loads a storage access list from a file.
    """
    access_list = parse_file_as(List[StorageAccess], filepath)
    access_list.sort(key=lambda access: len(cast(StorageAccess, access).storage_path))
    return access_list


def load_access_list_from_string(access_list_string: str):
    """
    Loads a storage access list from a JSON string (or bytes).
    """
    access_list = parse_raw_as(List[StorageAccess], access_list_string)
    access_list.sort(key=lambda access: len(cast(StorageAccess, access).storage_path))
    return access_list


def match_paths(
    access_type: AccessType, path_components: List[str], storage_access: StorageAccess
) -> Tuple[bool, Dict[str, str]]:
    """
    Checks if the components from a user-provided path match a given access authorization.

    If not a match, returns (False, {}).
    Else, returns (True, variable_bindings) where variable_bindings is a dictionary whose keys are of the form
    "var/<varname>" for all variables that occur in the registered_path, and the values are the values
    that should be substituted for the corresponding variables.
    """
    if storage_access.access != access_type:
        return (False, {})

    variable_bindings: Dict[str, str] = {}
    for i, registered_component in enumerate(storage_access.storage_path):
        if registered_component.startswith("var/"):
            variable_bindings[registered_component] = path_components[i]
        elif path_components[i] != registered_component:
            return (False, {})

    return (True, variable_bindings)


class AccessManager:
    """
    AccessManager maintains lists of access authorizations for storage paths.

    It also matches user-provided paths to the storage paths it matches.
    """

    def __init__(
        self, storage_access_list: List[StorageAccess], blockchains: BlockchainManager
    ) -> None:
        self.storage_access_list = storage_access_list
        self.blockchains = blockchains

    def match(
        self, access_type: AccessType, path: str
    ) -> List[Tuple[StorageAccess, Dict[str, str]]]:
        """
        Returns all access authorizations that apply to the given path. Each matching authorization comes
        with a binding of values for each variable component of that path.
        """
        path_components = path.split("/")
        matching_access_list: List[Tuple[StorageAccess, Dict[str, str]]] = []
        for storage_access in self.storage_access_list:
            is_match, variable_bindings = match_paths(
                access_type, path_components, storage_access
            )
            if is_match:
                matching_access_list.append((storage_access, variable_bindings))
        return matching_access_list

    def authorization(
        self, user_address: str, access_type: AccessType, path: str
    ) -> Optional[StorageAccess]:
        """
        If the user with the given address is authorized to make the given access_type on the given
        path, this function returns the first StorageAccess it encounters that grants them that
        authorization.

        Otherwise, if the user is not authorized for that access, it returns None.
        """
        possible_authorizations = self.match(access_type, path)
        for storage_access, variable_bindings in possible_authorizations:
            if (
                storage_access.authorization.authorization_type
                == AuthorizationType.PUBLIC
            ):
                return storage_access
            else:
                blockchain = self.blockchains.get(
                    storage_access.authorization.blockchain
                )
                if blockchain is None or not blockchain.healthy:
                    continue

                # Process contract_address, token_id, and minimum_balance with substitutions from
                # variable_bindings if necessary.
                contract_address = storage_access.authorization.contract_address
                if variable_bindings.get(contract_address) is not None:
                    contract_address = variable_bindings[contract_address]

                token_id = storage_access.authorization.token_id
                if variable_bindings.get(token_id) is not None:
                    token_id = variable_bindings[token_id]

                minimum_balance = storage_access.authorization.minimum_balance
                if variable_bindings.get(minimum_balance) is not None:
                    minimum_balance = int(variable_bindings[minimum_balance])

                if (
                    storage_access.authorization.authorization_type
                    == AuthorizationType.ERC20
                ):
                    contract = ERC20(blockchain.client, contract_address)
                    # Ignores token_id.
                    if contract.balanceOf(user_address) >= minimum_balance:
                        return storage_access
                elif (
                    storage_access.authorization.authorization_type
                    == AuthorizationType.ERC721
                ):
                    contract = ERC721(blockchain.client, contract_address)
                    # Ignores minimum_balance
                    if contract.ownerOf(token_id) == Web3.toChecksumAddress(
                        user_address
                    ):
                        return storage_access
                elif (
                    storage_access.authorization.authorization_type
                    == AuthorizationType.ERC1155
                ):
                    contract = ERC1155(blockchain.client, contract_address)
                    if contract.balanceOf(user_address, token_id) >= minimum_balance:
                        return storage_access

        return None
