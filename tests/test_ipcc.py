import ipaddress
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import URLError

import app.ipcc as ipcc_module
from app.ipcc import (
    FetchError,
    RIRParseError,
    collapse_networks,
    fetch_networks,
    parse_stream,
    save_networks,
)


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


def test_parse_non_cidr_ipv4_range():

    data = b"ripencc|US|ipv4|192.0.2.0|768|20240101|allocated\n"

    nets = list(
        parse_stream(
            BytesIO(data),
            country="US",
            ipv6=False,
        )
    )

    assert nets == [
        ipaddress.ip_network("192.0.2.0/23"),
        ipaddress.ip_network("192.0.4.0/24"),
    ]


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


def test_status_filtering():

    data = b"""
ripencc|US|ipv4|192.0.2.0|256|20240101|available
ripencc|US|ipv4|198.51.100.0|256|20240101|reserved
ripencc|US|ipv4|203.0.113.0|256|20240101|assigned
"""

    nets = list(
        parse_stream(
            BytesIO(data),
            country="US",
            ipv6=False,
        )
    )

    assert nets == [ipaddress.ip_network("203.0.113.0/24")]


def test_rejects_malformed_matching_record():

    data = b"""# delegated data
ripencc|US|ipv4|invalid|256|20240101|allocated
"""

    try:
        list(
            parse_stream(
                BytesIO(data),
                country="US",
                ipv6=False,
                source="ripencc",
            )
        )
    except RIRParseError as error:
        assert error.source == "ripencc"
        assert error.line_number == 2
        assert error.reason
        assert str(error).startswith("ripencc line 2:")
    else:
        raise AssertionError("RIRParseError was not raised")


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


def test_save_networks_replaces_output_atomically():

    with TemporaryDirectory() as directory:
        output = Path(directory) / "us.zone"
        output.write_text("old data\n")

        save_networks(
            [
                ipaddress.ip_network("192.0.2.0/24"),
                ipaddress.ip_network("10.0.0.0/8"),
            ],
            output,
        )

        assert output.read_text() == "10.0.0.0/8\n192.0.2.0/24\n"
        assert list(output.parent.iterdir()) == [output]


def test_save_networks_preserves_output_on_failure():

    with TemporaryDirectory() as directory:
        output = Path(directory) / "us.zone"
        output.write_text("complete data\n")

        with patch.object(
            ipcc_module.os,
            "replace",
            side_effect=OSError("replace failed"),
        ):
            try:
                save_networks(
                    [ipaddress.ip_network("192.0.2.0/24")],
                    output,
                )
            except OSError as error:
                assert str(error) == "replace failed"
            else:
                raise AssertionError("OSError was not raised")

        assert output.read_text() == "complete data\n"
        assert list(output.parent.iterdir()) == [output]


def test_fetch_networks_rejects_partial_results():

    def urlopen(url, timeout):

        assert timeout == ipcc_module.TIMEOUT

        if url == "broken":
            raise URLError("unavailable")

        return BytesIO(FAKE_DATA)

    with (
        patch.object(ipcc_module, "URLS", {"working": "working", "broken": "broken"}),
        patch.object(ipcc_module.urllib.request, "urlopen", side_effect=urlopen),
    ):
        try:
            fetch_networks("US", ipv6=False)
        except FetchError as error:
            assert error.registries == ("broken",)
        else:
            raise AssertionError("FetchError was not raised")


def test_fetch_networks_rejects_malformed_source():

    data = b"ripencc|US|ipv4|invalid|256|20240101|allocated\n"

    with (
        patch.object(ipcc_module, "URLS", {"ripencc": "source"}),
        patch.object(
            ipcc_module.urllib.request,
            "urlopen",
            return_value=BytesIO(data),
        ),
    ):
        try:
            fetch_networks("US", ipv6=False)
        except FetchError as error:
            assert error.registries == ("ripencc",)
        else:
            raise AssertionError("FetchError was not raised")


def test_main_does_not_save_partial_results():

    args = SimpleNamespace(
        country="US",
        ipv6=False,
        output="us.zone",
        verbose=False,
    )

    with (
        patch.object(ipcc_module, "parse_args", return_value=args),
        patch.object(ipcc_module, "setup_logging"),
        patch.object(
            ipcc_module,
            "fetch_networks",
            side_effect=FetchError(["arin"]),
        ),
        patch.object(ipcc_module, "save_networks") as save_networks,
    ):
        try:
            ipcc_module.main()
        except SystemExit as error:
            assert error.code == 1
        else:
            raise AssertionError("SystemExit was not raised")

    save_networks.assert_not_called()
