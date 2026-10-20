"""netcalc - a small subnet calculator for IPv4 and IPv6."""

__version__ = "0.1.0"

from .core import (
    NetcalcError,
    contains,
    host_range,
    parse_address,
    parse_network,
    split,
    summarize,
    usable_hosts,
)

__all__ = [
    "__version__",
    "NetcalcError",
    "contains",
    "host_range",
    "parse_address",
    "parse_network",
    "split",
    "summarize",
    "usable_hosts",
]
