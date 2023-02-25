"""
Access control layer for blobs3
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, parse_file_as, parse_raw_as, validator
from web3 import Web3


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
    return parse_file_as(List[StorageAccess], filepath)


def load_access_list_from_string(access_list_string: str):
    """
    Loads a storage access list from a JSON string (or bytes).
    """
    return parse_raw_as(List[StorageAccess], access_list_string)


def match_paths(
    path_components: List[str], storage_access: StorageAccess
) -> Tuple[bool, Dict[str, str]]:
    """
    Checks if the components from a user-provided path match a given access authorization.

    If not a match, returns (False, {}).
    Else, returns (True, variable_bindings) where variable_bindings is a dictionary whose keys are of the form
    "var/<varname>" for all variables that occur in the registered_path, and the values are the values
    that should be substituted for the corresponding variables.
    """
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

    def __init__(self, storage_access_list: List[StorageAccess]) -> None:
        self.storage_access_list = storage_access_list

    def match(self, path: str) -> List[Tuple[StorageAccess, Dict[str, str]]]:
        """
        Returns all access authorizations that apply to the given path. Each matching authorization comes
        with a binding of values for each variable component of that path.
        """
        path_components = path.split("/")
        for storage_access in self.storage_access_list:
            pass
