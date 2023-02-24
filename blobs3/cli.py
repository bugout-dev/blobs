import argparse

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

    return parser


def main():
    parser = generate_cli()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
