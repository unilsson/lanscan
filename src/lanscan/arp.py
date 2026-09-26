import re
import subprocess
import sys
from collections import defaultdict
from ipaddress import IPv4Address

from .models import ArpDevice


ARP_RE = re.compile(
    r"^(?P<ip>\d+\.\d+\.\d+\.\d+)\s+"
    r"(?P<mac>[0-9a-fA-F:]{17})\s*"
    r"(?P<vendor>.*)$"
)


def parse_arp_scan_output(output: str, hosts=None):
    """Parse arp-scan output and merge unique devices by IP and MAC."""
    if hosts is None:
        hosts = defaultdict(list)

    for line in output.splitlines():
        match = ARP_RE.match(line)

        if not match:
            continue

        ip = IPv4Address(match.group("ip"))
        mac = match.group("mac").lower()
        vendor = match.group("vendor").strip()

        if any(device.mac == mac for device in hosts[ip]):
            continue

        hosts[ip].append(
            ArpDevice(
                ip=ip,
                mac=mac,
                vendor=vendor,
            )
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
