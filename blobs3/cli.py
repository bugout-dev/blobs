import argparse

from . import metadata
from .version import VERSION


def generate_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="blobs3: Blob storage with web3 access control"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=VERSION,
        help="Print the blobs3 version",
    )
    parser.set_defaults(func=lambda _: parser.print_help())

    subparsers = parser.add_subparsers()

    metadata_parser = metadata.generate_cli()
    subparsers.add_parser("metadata", parents=[metadata_parser], add_help=False)

    return parser


def main():
    parser = generate_cli()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
