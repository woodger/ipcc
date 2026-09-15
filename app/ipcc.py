"""Generate complete, aggregated country CIDR lists from RIR data."""

import ipaddress
import logging
import sys
import urllib.request

from app.args import parse_args


URLS = {
    "ripencc": "https://ftp.ripe.net/pub/stats/ripencc/delegated-ripencc-latest",
    "arin": "https://ftp.arin.net/pub/stats/arin/delegated-arin-extended-latest",
    "apnic": "https://ftp.apnic.net/pub/stats/apnic/delegated-apnic-latest",
    "lacnic": "https://ftp.lacnic.net/pub/stats/lacnic/delegated-lacnic-latest",
    "afrinic": "https://ftp.afrinic.net/pub/stats/afrinic/delegated-afrinic-latest",
}

TIMEOUT = 30


class FetchError(RuntimeError):
    """Report registries whose delegated data could not be read."""

    def __init__(self, registries):

        self.registries = tuple(registries)

        super().__init__(
            f"Failed to download RIR data: {', '.join(self.registries)}"
        )


def setup_logging(verbose):
    """Configure concise CLI logging at the requested verbosity."""

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(message)s",
    )


def prefix_v4(count):
    """Convert a power-of-two IPv4 address count to a CIDR prefix length."""

    # One CIDR can represent only a positive power-of-two address count.
    if count <= 0 or (count & (count - 1)):
        raise ValueError(count)

    return 32 - (count.bit_length() - 1)


def parse_stream(stream, country, ipv6):
    """Yield matching networks from a byte-oriented RIR delegated stream."""

    want = "ipv6" if ipv6 else "ipv4"

    for raw in stream:

        line = raw.decode().strip()

        if not line or line[0] == "#":
            continue

        parts = line.split("|")

        if len(parts) < 7:
            continue

        _, cc, iptype, start, value, *_ = parts

        if cc != country or iptype != want:
            continue

        try:

            # RIR records store an IPv6 prefix length but an IPv4 address count.
            if ipv6:

                yield ipaddress.ip_network(
                    f"{start}/{int(value)}",
                    strict=False,
                )

            else:

                yield ipaddress.ip_network(
                    f"{start}/{prefix_v4(int(value))}",
                    strict=False,
                )

        except ValueError:

            logging.debug("Bad entry skipped")


def fetch_networks(country, ipv6):
    """Collect networks from every RIR or reject the incomplete result."""

    networks = []
    failed = []

    for name, url in URLS.items():

        logging.info(f"Downloading {name}...")

        try:

            with urllib.request.urlopen(url, timeout=TIMEOUT) as r:

                networks.extend(
                    parse_stream(r, country, ipv6)
                )

        except Exception as e:

            logging.warning(f"{name} failed: {e}")

            failed.append(name)

    if failed:

        # Partial data must never overwrite a previously complete output file.
        raise FetchError(failed)

    return networks


def collapse_networks(networks):
    """Merge overlapping and adjacent networks into the smallest CIDR list."""

    logging.info(f"Collected: {len(networks)}")

    collapsed = list(
        ipaddress.collapse_addresses(networks)
    )

    logging.info(f"Collapsed: {len(collapsed)}")

    return collapsed


def save_networks(networks, filename):
    """Write networks in ascending address order, one CIDR per line."""

    networks = sorted(
        networks,
        key=lambda n: int(n.network_address),
    )

    with open(filename, "w") as f:

        for net in networks:

            f.write(f"{net}\n")


def validate_country(country):
    """Normalize a two-letter country code or reject its shape."""

    if len(country) != 2 or not country.isalpha():

        raise ValueError(
            "Country must be ISO-3166 alpha-2 code"
        )

    return country.upper()


def main():
    """Run the command-line workflow."""

    args = parse_args()

    setup_logging(args.verbose)

    try:

        country = validate_country(args.country)

    except ValueError as e:

        logging.error(e)
        sys.exit(1)

    output = args.output or f"{country.lower()}.zone"

    try:

        networks = fetch_networks(
            country,
            args.ipv6,
        )

    except FetchError as e:

        logging.error(e)
        sys.exit(1)

    if not networks:

        logging.error("No networks found")
        sys.exit(1)

    collapsed = collapse_networks(networks)

    save_networks(
        collapsed,
        output,
    )

    logging.info(f"Done: {output}")


if __name__ == "__main__":
    main()
