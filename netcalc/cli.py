"""Command-line interface for netcalc."""

from __future__ import annotations

import argparse
import json
import sys
from itertools import islice
from typing import List, Optional

from . import __version__
from .core import NetcalcError, contains, parse_address, parse_network, split, summarize

DEFAULT_SPLIT_LIMIT = 64


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="netcalc",
        description="Subnet calculator for IPv4 and IPv6 networks.",
    )
    parser.add_argument("--version", action="version", version=f"netcalc {__version__}")
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable JSON instead of a table",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_info = sub.add_parser("info", help="show details of a network")
    p_info.add_argument("network", help="e.g. 192.168.10.0/24 or 2001:db8::/48")

    p_split = sub.add_parser("split", help="split a network into smaller subnets")
    p_split.add_argument("network", help="the network to split")
    p_split.add_argument(
        "new_prefix", type=int, help="target prefix length, e.g. 26"
    )
    p_split.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_SPLIT_LIMIT,
        help=f"maximum subnets to print (default: {DEFAULT_SPLIT_LIMIT}, 0 = no limit)",
    )

    p_check = sub.add_parser("check", help="test whether an address is in a network")
    p_check.add_argument("network", help="the network to test against")
    p_check.add_argument("address", help="the IP address to look for")

    return parser


def _print_table(data: dict) -> None:
    width = max(len(key) for key in data)
    for key, value in data.items():
        print(f"{key.replace('_', ' '):<{width}}  {value}")


def cmd_info(args: argparse.Namespace) -> int:
    net = parse_network(args.network)
    data = summarize(net)
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        _print_table(data)
    return 0


def cmd_split(args: argparse.Namespace) -> int:
    net = parse_network(args.network)
    subnets = split(net, args.new_prefix)

    if args.limit < 0:
        raise NetcalcError("--limit cannot be negative")
    # Take one extra item so we can tell the user the output was truncated.
    taken = list(subnets) if args.limit == 0 else list(islice(subnets, args.limit + 1))
    truncated = args.limit != 0 and len(taken) > args.limit
    if truncated:
        taken = taken[: args.limit]

    if args.json:
        print(
            json.dumps(
                {
                    "network": str(net),
                    "new_prefix": args.new_prefix,
                    "returned": len(taken),
                    "truncated": truncated,
                    "subnets": [str(s) for s in taken],
                },
                indent=2,
            )
        )
    else:
        for subnet in taken:
            print(subnet)
        if truncated:
            print(
                f"... truncated at {args.limit} subnets; "
                "raise or disable the cap with --limit",
                file=sys.stderr,
            )
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    net = parse_network(args.network)
    addr = parse_address(args.address)
    inside = contains(net, addr)
    if args.json:
        print(
            json.dumps(
                {"network": str(net), "address": str(addr), "contains": inside},
                indent=2,
            )
        )
    else:
        verdict = "is inside" if inside else "is NOT inside"
        print(f"{addr} {verdict} {net}")
    # Exit code 1 on a negative result, so the command is usable in shell tests.
    return 0 if inside else 1


COMMANDS = {"info": cmd_info, "split": cmd_split, "check": cmd_check}


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return COMMANDS[args.command](args)
    except NetcalcError as exc:
        print(f"netcalc: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
