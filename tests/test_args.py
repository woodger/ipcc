import sys
from unittest.mock import patch

from app.args import parse_args


def test_defaults():

    with patch.object(sys, "argv", ["ipcc"]):
        args = parse_args()

    assert args.country == "RU"
    assert args.ipv6 is False
    assert args.output is None
    assert args.verbose is False


def test_all_options():

    argv = [
        "ipcc",
        "--country",
        "US",
        "--ipv6",
        "--output",
        "us.zone",
        "--verbose",
    ]

    with patch.object(sys, "argv", argv):
        args = parse_args()

    assert args.country == "US"
    assert args.ipv6 is True
    assert args.output == "us.zone"
    assert args.verbose is True
