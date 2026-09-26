#!/usr/bin/env python3

import argparse
import sys

from .arp import find_conflicts, parse_arp_scan_output, run_arp_scan
from .dns import resolve_hostnames
from .output import print_all, print_devices, print_json


def build_parser():
    parser = argparse.ArgumentParser(
        description="Discover devices, hostnames and IP conflicts on a local LAN"
    )

    parser.add_argument(
        "network",
        nargs="?",
        help="Network to scan, for example 192.168.1.0/24",
    )

    view = parser.add_mutually_exclusive_group()

    view.add_argument(
        "--all",
        action="store_true",
        help="Show used and apparently free IP addresses",
    )

    view.add_argument(
        "--conflicts",
        action="store_true",
        help="Show only IP addresses seen with multiple MAC addresses",
    )

    parser.add_argument(
        "--passes",
        type=int,
        help="Number of ARP sweeps to perform (default: 3 with --conflicts, otherwise 1)",
    )

    parser.add_argument(
        "--no-dns",
        action="store_true",
        help="Do not perform reverse hostname lookups",
    )

    parser.add_argument(
        "--dns-timeout",
        type=float,
        default=1.0,
        help="Timeout in seconds for each reverse lookup (default: 1.0)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.all and not args.network:
        parser.error("--all requires an explicit network")

    if args.passes is not None and args.passes < 1:
        parser.error("--passes must be at least 1")

    if args.dns_timeout <= 0:
        parser.error("--dns-timeout must be greater than 0")

    passes = args.passes if args.passes is not None else (3 if args.conflicts else 1)
    hosts = run_arp_scan(args.network, passes=passes)

    if args.conflicts:
        hosts = find_conflicts(hosts)

    hostnames = (
        {}
        if args.no_dns
        else resolve_hostnames(hosts.keys(), timeout=args.dns_timeout)
    )

    if args.json:
        print_json(hosts, hostnames)
    elif args.all:
        print_all(args.network, hosts, hostnames)
    else:
        print_devices(hosts, hostnames)

    if args.conflicts and hosts:
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
