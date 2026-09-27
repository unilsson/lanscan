#!/usr/bin/env python3

import argparse
import sys

from .arp import find_conflicts, parse_arp_scan_output, run_arp_scan
from .config import ConfigError, load_opnsense_config
from .dns import resolve_hostnames
from .opnsense import OpnsenseError, fetch_dhcp_leases, leases_in_network
from .output import (
    print_all,
    print_devices,
    print_free,
    print_json,
    print_summary,
    print_summary_json,
)


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Discover LAN devices and correlate ARP, reverse DNS and "
            "OPNsense DHCP allocation data"
        )
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
        help="Show used, conflicting, leased, reserved and apparently free IP addresses",
    )

    view.add_argument(
        "--free",
        action="store_true",
        help="Show only apparently free IP addresses",
    )

    view.add_argument(
        "--summary",
        action="store_true",
        help="Show address allocation counts for the network",
    )

    view.add_argument(
        "--conflicts",
        action="store_true",
        help="Show only IP addresses seen with multiple MAC addresses",
    )

    parser.add_argument(
        "--opnsense",
        action="store_true",
        help=(
            "Correlate results with OPNsense ISC DHCPv4 dynamic leases "
            "and static mappings"
        ),
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

    if (args.all or args.free or args.summary) and not args.network:
        parser.error("--all, --free and --summary require an explicit network")

    if args.opnsense and not args.network:
        parser.error("--opnsense requires an explicit network")

    if args.passes is not None and args.passes < 1:
        parser.error("--passes must be at least 1")

    if args.dns_timeout <= 0:
        parser.error("--dns-timeout must be greater than 0")

    leases = None

    if args.opnsense:
        try:
            config = load_opnsense_config()
            leases = leases_in_network(
                args.network,
                fetch_dhcp_leases(config),
            )
        except (ConfigError, OpnsenseError) as exc:
            print(f"lanscan: {exc}", file=sys.stderr)
            return 1

    passes = args.passes if args.passes is not None else (3 if args.conflicts else 1)
    hosts = run_arp_scan(args.network, passes=passes)

    if args.conflicts:
        hosts = find_conflicts(hosts)
        if leases is not None:
            leases = {
                ip: lease
                for ip, lease in leases.items()
                if ip in hosts
            }

    lookup_ips = set(hosts)
    if leases:
        lookup_ips.update(leases)

    hostnames = (
        {}
        if args.no_dns or args.free or args.summary
        else resolve_hostnames(lookup_ips, timeout=args.dns_timeout)
    )

    if args.summary:
        if args.json:
            print_summary_json(args.network, hosts, leases)
        else:
            print_summary(args.network, hosts, leases)
    elif args.json:
        print_json(
            hosts,
            hostnames,
            network=args.network,
            include_free=args.all,
            free_only=args.free,
            leases=leases,
        )
    elif args.free:
        print_free(args.network, hosts, leases)
    elif args.all:
        print_all(args.network, hosts, hostnames, leases)
    else:
        print_devices(hosts, hostnames, leases)

    if args.conflicts and hosts:
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
