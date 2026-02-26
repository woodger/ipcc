import ipaddress
from io import BytesIO

from app.ipcc import parse_stream, collapse_networks


FAKE_DATA = b"""
ripencc|US|ipv4|5.8.0.0|8192|20240101|allocated
ripencc|US|ipv4|5.16.0.0|4096|20240101|allocated
ripencc|US|ipv4|5.20.0.0|4096|20240101|allocated
ripencc|DE|ipv4|1.1.1.0|256|20240101|allocated
ripencc|US|ipv6|2a00::|32|20240101|allocated
"""


def test_parse_ipv4():

    nets = list(
        parse_stream(
            BytesIO(FAKE_DATA),
            country="US",
            ipv6=False,
        )
    )

    assert len(nets) == 3

    assert ipaddress.ip_network("5.8.0.0/19") in nets
    assert ipaddress.ip_network("5.16.0.0/20") in nets
    assert ipaddress.ip_network("5.20.0.0/20") in nets


def test_parse_ipv6():

    nets = list(
        parse_stream(
            BytesIO(FAKE_DATA),
            country="US",
            ipv6=True,
        )
    )

    assert len(nets) == 1

    assert ipaddress.ip_network("2a00::/32") in nets


def test_country_filtering():

    nets = list(
        parse_stream(
            BytesIO(FAKE_DATA),
            country="DE",
            ipv6=False,
        )
    )

    assert len(nets) == 1

    assert ipaddress.ip_network("1.1.1.0/24") in nets


def test_collapse_networks():

    data = b"""
ripencc|US|ipv4|10.0.0.0|4096|20240101|allocated
ripencc|US|ipv4|10.0.16.0|4096|20240101|allocated
"""

    nets = list(
        parse_stream(
            BytesIO(data),
            country="US",
            ipv6=False,
        )
    )

    collapsed = collapse_networks(nets)

    assert len(collapsed) == 1

    assert collapsed[0] == ipaddress.ip_network("10.0.0.0/19")
