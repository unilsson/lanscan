#!/usr/bin/env python3

import argparse
import ipaddress
import json
import re
import subprocess
import sys
from collections import defaultdict


ARP_RE = re.compile(
    r"^(?P<ip>\d+\.\d+\.\d+\.\d+)\s+"
    r"(?P<mac>[0-9a-fA-F:]{17})\s*"
    r"(?P<vendor>.*)$"
)


def parse_arp_scan_output(output: str, hosts=None):
    """Parse arp-scan output and merge hosts by IP and MAC address."""
    if hosts is None:
        hosts = defaultdict(list)

    for line in output.splitlines():
        match = ARP_RE.match(line)

        if not match:
            continue

        ip = ipaddress.ip_address(match.group("ip"))
        mac = match.group("mac").lower()
        vendor = match.group("vendor").strip()

        if any(device["mac"] == mac for device in hosts[ip]):
            continue

        hosts[ip].append(
            {
                "ip": str(ip),
                "mac": mac,
                "vendor": vendor,
            }
        )

    return hosts


def run_arp_scan(network: str | None, passes: int = 1):
    """Run arp-scan one or more times and merge unique replies."""
    hosts = defaultdict(list)

    cmd = ["sudo", "arp-scan"]
    if network:
        cmd.append(network)
    else:
        cmd.append("--localnet")

    for _ in range(passes):
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            sys.exit(result.returncode)

        parse_arp_scan_output(result.stdout, hosts)

    return dict(hosts)


def find_conflicts(hosts):
    """Return IP addresses that were seen with more than one MAC address."""
    return {
        ip: devices
        for ip, devices in hosts.items()
        if len(devices) > 1
    }


def host_status(devices):
    return "CONFLICT" if len(devices) > 1 else "USED"


def print_devices(hosts):
    for ip in sorted(hosts):
        devices = hosts[ip]
        status = host_status(devices)

        for index, device in enumerate(devices):
            ip_text = str(ip) if index == 0 else ""
            status_text = status if index == 0 else ""

            print(
                f"{ip_text:15}  "
                f"{status_text:8}  "
                f"{device['mac']:17}  "
                f"{device['vendor']}"
            )


def print_all(network, hosts):
    net = ipaddress.ip_network(network, strict=False)

    for ip in net.hosts():
        if ip not in hosts:
            print(f"{str(ip):15}  FREE")
            continue

        devices = hosts[ip]
        status = host_status(devices)

        for index, device in enumerate(devices):
            ip_text = str(ip) if index == 0 else ""
            status_text = status if index == 0 else ""

            print(
                f"{ip_text:15}  "
                f"{status_text:8}  "
                f"{device['mac']:17}  "
                f"{device['vendor']}"
            )


def print_json(hosts):
    data = []

    for ip in sorted(hosts):
        devices = hosts[ip]

        data.append(
            {
                "ip": str(ip),
                "status": host_status(devices).lower(),
                "devices": devices,
            }
        )

    print(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Discover devices and IP conflicts on a local LAN using ARP"
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
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    if args.all and not args.network:
        parser.error("--all requires an explicit network")

    if args.passes is not None and args.passes < 1:
        parser.error("--passes must be at least 1")

    passes = args.passes if args.passes is not None else (3 if args.conflicts else 1)
    hosts = run_arp_scan(args.network, passes=passes)

    if args.conflicts:
        hosts = find_conflicts(hosts)

    if args.json:
        print_json(hosts)
    elif args.all:
        print_all(args.network, hosts)
    else:
        print_devices(hosts)

    if args.conflicts and hosts:
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
