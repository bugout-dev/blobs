"""
Functions that perform updates to ERC721-style metadata in S3 blobs
"""

import argparse
import json
from typing import Any, Dict, Protocol, Tuple

import boto3

class S3Client(Protocol):
    def get_object(*args, **kwargs) -> Dict[str, Any]:
        ...

    def put_object(*args, **kwargs) -> Dict[str, Any]:
        ...

def split_s3_uri(s3_uri: str) -> Tuple[str, str]:
    """
    Splits S3 URI into a bucket name and a path key.

    Returns a tuple (bucket, key) - both strings.
    """
    if s3_uri.startswith("s3://"):
        s3_uri = s3_uri[5:]

    bucket, key = s3_uri.split("/", 1)
    return bucket, key

def get_metadata(s3_client, s3_uri: str) -> Dict[str, Any]:
    """
    Get JSON metadata from a blob in S3
    """
    bucket, key = split_s3_uri(s3_uri)
    response = s3_client.get_object(Bucket=bucket, Key=key)
    body = json.loads(response["Body"].read())
    return body

def update_metadata(s3_client, s3_uri: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Replace the metadata at the given S3 URI with the given dictionary. If the blob at that URI does
    not exist, this creates it.
    """
    bucket, key = split_s3_uri(s3_uri)
    response = s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(metadata),
        ContentType="application/json",
    )
    return response

def change_name(s3_client, s3_uri: str, new_name: str) -> Dict[str, Any]:
    """
    Change the name in the metadata at the given S3 URI to the given string.
    """
    metadata = get_metadata(s3_client, s3_uri)
    old_name = metadata.get("name")
    if old_name is None or old_name != new_name:
        metadata["name"] = new_name
        return update_metadata(s3_client, s3_uri, metadata)
    return {}

def add_trait(s3_client, s3_uri: str, trait_type: str, value: Any, expect_unique: bool = False) -> Dict[str, Any]:
    """
    Appends the given trait_type to the attributes array in the metadata at the given S3 URI. If expect_unique is True,
    then this will raise an exception if the trait_type already exists in the attributes array. Otherwise,
    it just adds the trait.
    """
    metadata = get_metadata(s3_client, s3_uri)
    if metadata.get("attributes") is None:
        metadata["attributes"] = []

    if expect_unique:
        for attribute in metadata["attributes"]:
            if attribute.get("trait_type") == trait_type:
                raise ValueError(f"Trait type {trait_type} already exists in attributes array")

    metadata["attributes"].append({"trait_type": trait_type, "value": value})

    return update_metadata(s3_client, s3_uri, metadata)

def handle_get_metadata(args: argparse.Namespace) -> None:
    s3_client = boto3.client("s3")
    metadata = get_metadata(s3_client, args.s3_uri)
    print(json.dumps(metadata, indent=4))

def handle_update_metadata(args: argparse.Namespace) -> None:
    s3_client = boto3.client("s3")
    with open(args.metadata) as f:
        metadata = json.load(f)
    response = update_metadata(s3_client, args.s3_uri, metadata)
    print(json.dumps(response, indent=4))

def handle_change_name(args: argparse.Namespace) -> None:
    s3_client = boto3.client("s3")
    response = change_name(s3_client, args.s3_uri, args.name)
    print(json.dumps(response, indent=4))

def handle_add_trait(args: argparse.Namespace) -> None:
    s3_client = boto3.client("s3")
    response = add_trait(s3_client, args.s3_uri, args.trait_type, args.value, args.expect_unique)
    print(json.dumps(response, indent=4))

def generate_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("Interact with S3 metadata")
    parser.set_defaults(func=lambda _: parser.print_help())

    subparsers = parser.add_subparsers()

    get_parser = subparsers.add_parser("get", help="Get metadata from S3")
    get_parser.add_argument("s3_uri", help="S3 URI to get metadata from")
    get_parser.set_defaults(func=handle_get_metadata)

    update_parser = subparsers.add_parser("update", help="Update metadata in S3")
    update_parser.add_argument("s3_uri", help="S3 URI to update metadata in")
    update_parser.add_argument("-d", "--metadata", required=True, help="Path to JSON metadata")
    update_parser.set_defaults(func=handle_update_metadata)

    change_name_parser = subparsers.add_parser("change-name", help="Change the name in the metadata at the given S3 URI")
    change_name_parser.add_argument("s3_uri", help="S3 URI to update metadata in")
    change_name_parser.add_argument("--name", "-n", help="New name to set in the metadata")
    change_name_parser.set_defaults(func=handle_change_name)

    add_trait_parser = subparsers.add_parser("add-trait", help="Add a trait to the attributes array in the metadata at the given S3 URI")
    add_trait_parser.add_argument("s3_uri", help="S3 URI to update metadata in")
    add_trait_parser.add_argument("--trait-type", "-t", required=True, help="Trait type to add")
    add_trait_parser.add_argument("--value", "-v", required=True, help="Value to add")
    add_trait_parser.add_argument("--expect-unique", action="store_true", help="Raise an exception if the trait type already exists in the attributes array")
    add_trait_parser.set_defaults(func=handle_add_trait)

    return parser
