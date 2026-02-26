import argparse


def parse_args():

    parser = argparse.ArgumentParser(
        description="Generate aggregated CIDR blocks per country from RIR delegated lists"
    )

    parser.add_argument(
        "--country",
        default="RU",
        help="ISO 3166-1 alpha-2 country code (default: RU)",
    )

    parser.add_argument(
        "--ipv6",
        action="store_true",
        help="Generate IPv6 blocks instead of IPv4",
    )

    parser.add_argument(
        "--output",
        help="Output filename (default: <country>.zone)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()
