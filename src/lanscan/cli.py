#!/usr/bin/env python3

import argparse
import ipaddress
import json
import re
import subprocess
import sys


ARP_RE = re.compile(
    r"^(?P<ip>\d+\.\d+\.\d+\.\d+)\s+"
    r"(?P<mac>[0-9a-fA-F:]{17})\s*"
    r"(?P<vendor>.*)$"
)


def run_arp_scan(network: str | None):
    cmd = ["sudo", "arp-scan"]

    if network:
        cmd.append(network)
    else:
        cmd.append("--localnet")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    hosts = {}

    for line in result.stdout.splitlines():
        match = ARP_RE.match(line)

        if not match:
            continue

        ip = ipaddress.ip_address(match.group("ip"))

        hosts[ip] = {
            "ip": str(ip),
            "mac": match.group("mac").lower(),
            "vendor": match.group("vendor").strip(),
        }

    return hosts


def print_used(hosts):
    for ip in sorted(hosts):
        host = hosts[ip]

        print(
            f"{str(ip):15}  "
            f"{host['mac']:17}  "
            f"{host['vendor']}"
        )


def print_all(network, hosts):
    net = ipaddress.ip_network(network, strict=False)

    for ip in net.hosts():
        if ip in hosts:
            host = hosts[ip]

            print(
                f"{str(ip):15}  "
                f"USED  "
                f"{host['mac']:17}  "
                f"{host['vendor']}"
            )
        else:
            print(f"{str(ip):15}  FREE")


def main():
    parser = argparse.ArgumentParser(
        description="Discover devices on a local LAN using ARP"
    )

    parser.add_argument(
        "network",
        nargs="?",
        help="Network to scan, for example 192.168.1.0/24",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Show used and apparently free IP addresses",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output discovered hosts as JSON",
    )

    args = parser.parse_args()

    if args.all and not args.network:
        parser.error("--all requires an explicit network")

    hosts = run_arp_scan(args.network)

    if args.json:
        data = [hosts[ip] for ip in sorted(hosts)]
        print(json.dumps(data, indent=2))
        return

    if args.all:
        print_all(args.network, hosts)
    else:
        print_used(hosts)


if __name__ == "__main__":
    main()
