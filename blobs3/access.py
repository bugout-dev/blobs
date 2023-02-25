"""
Access control layer for blobs3
"""

from enum import Enum
from typing import List, Optional

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
    token_id: Optional[int] = None
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
    storage_path: List[str]
    authorization: AuthorizationSpecification
    access: AccessType

    @validator(storage_path)
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
