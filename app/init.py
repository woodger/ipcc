"""Compatibility exports for the original helper names."""

from .ipcc import (
    collapse_networks,
    fetch_networks as fetch_data,
    parse_stream as parse_networks,
    prefix_v4 as count_to_prefix_v4,
)


__all__ = [
    "collapse_networks",
    "count_to_prefix_v4",
    "fetch_data",
    "parse_networks",
]
