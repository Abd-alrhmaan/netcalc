"""Core subnet calculations.

Everything here is built on the standard-library ``ipaddress`` module, so the
package has zero third-party dependencies. The functions are deliberately pure:
they take strings or ``ipaddress`` objects and return plain Python values, which
keeps them easy to unit-test and to reuse from other code.
"""

from __future__ import annotations

import ipaddress
from typing import Any, Dict, Iterator, Tuple, Union

IPNetwork = Union[ipaddress.IPv4Network, ipaddress.IPv6Network]
IPAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]

__all__ = [
    "NetcalcError",
    "parse_network",
    "parse_address",
    "usable_hosts",
    "host_range",
    "summarize",
    "split",
    "contains",
]


class NetcalcError(ValueError):
    """Raised when input cannot be interpreted as a network or an address."""


def parse_network(value: str, strict: bool = False) -> IPNetwork:
    """Parse ``192.168.1.10/24`` or ``2001:db8::/48`` into a network object.

    With ``strict=False`` (the default) host bits are allowed and silently
    masked off, which is what people usually type. Pass ``strict=True`` to
    reject an address that is not the network address of its own prefix.
    """
    try:
        return ipaddress.ip_network(value.strip(), strict=strict)
    except ValueError as exc:
        raise NetcalcError(f"invalid network {value!r}: {exc}") from exc


def parse_address(value: str) -> IPAddress:
    """Parse a bare IPv4 or IPv6 address."""
    try:
        return ipaddress.ip_address(value.strip())
    except ValueError as exc:
        raise NetcalcError(f"invalid IP address {value!r}: {exc}") from exc


def usable_hosts(net: IPNetwork) -> int:
    """Number of addresses that can actually be assigned to hosts.

    IPv4 normally loses the network and broadcast addresses, except for /31
    (RFC 3021 point-to-point links) and /32 (a single host route). IPv6 has no
    broadcast address, so the whole block counts.
    """
    if net.version == 4:
        if net.prefixlen == 32:
            return 1
        if net.prefixlen == 31:
            return 2
        return net.num_addresses - 2
    return net.num_addresses


def host_range(net: IPNetwork) -> Tuple[IPAddress, IPAddress]:
    """Return the (first, last) assignable address of ``net``."""
    if net.version == 4 and net.prefixlen <= 30:
        return (
            net.network_address + 1,
            net.broadcast_address - 1,
        )
    return net.network_address, net.broadcast_address


def summarize(net: IPNetwork) -> Dict[str, Any]:
    """Build a flat dictionary describing ``net``.

    The keys are stable and JSON-serialisable, so the CLI can print them as a
    table or dump them with ``--json`` without any extra formatting logic.
    """
    first, last = host_range(net)
    data: Dict[str, Any] = {
        "network": str(net.network_address),
        "prefix_length": net.prefixlen,
        "cidr": str(net),
        "netmask": str(net.netmask),
        "version": net.version,
        "first_host": str(first),
        "last_host": str(last),
        "total_addresses": net.num_addresses,
        "usable_hosts": usable_hosts(net),
        "is_private": net.is_private,
    }
    if net.version == 4:
        data["wildcard"] = str(net.hostmask)
        data["broadcast"] = str(net.broadcast_address)
    return data


def split(net: IPNetwork, new_prefix: int) -> Iterator[IPNetwork]:
    """Lazily yield the subnets of ``net`` at prefix length ``new_prefix``.

    This is a generator on purpose: splitting 10.0.0.0/8 into /30s is over 4
    million networks, and materialising that list would exhaust memory. Callers
    decide how many results they actually consume.
    """
    if new_prefix < net.prefixlen:
        raise NetcalcError(
            f"new prefix /{new_prefix} is larger than the network /{net.prefixlen}"
        )
    if new_prefix > net.max_prefixlen:
        raise NetcalcError(
            f"new prefix /{new_prefix} exceeds the maximum /{net.max_prefixlen} "
            f"for IPv{net.version}"
        )
    return net.subnets(new_prefix=new_prefix)


def contains(net: IPNetwork, addr: IPAddress) -> bool:
    """Return True if ``addr`` falls inside ``net``."""
    if net.version != addr.version:
        raise NetcalcError(
            f"cannot check an IPv{addr.version} address against an "
            f"IPv{net.version} network"
        )
    return addr in net
