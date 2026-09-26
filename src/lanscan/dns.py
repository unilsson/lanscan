import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from ipaddress import IPv4Address
from typing import Iterable


def parse_getent_output(output: str) -> str | None:
    """Return the canonical hostname from getent hosts output."""
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            return parts[1].rstrip(".")

    return None


def resolve_hostname(ip: IPv4Address, timeout: float = 1.0) -> str | None:
    """Resolve one IPv4 address through the system NSS resolver."""
    try:
        result = subprocess.run(
            ["getent", "hosts", str(ip)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None

    if result.returncode != 0:
        return None

    return parse_getent_output(result.stdout)


def resolve_hostnames(
    ips: Iterable[IPv4Address],
    timeout: float = 1.0,
    workers: int = 16,
):
    """Resolve many addresses concurrently so failed DNS does not stall a scan."""
    addresses = list(ips)

    if not addresses:
        return {}

    if shutil.which("getent") is None:
        return {ip: None for ip in addresses}

    results = {ip: None for ip in addresses}

    with ThreadPoolExecutor(max_workers=min(workers, len(addresses))) as executor:
        futures = {
            executor.submit(resolve_hostname, ip, timeout): ip
            for ip in addresses
        }

        for future in as_completed(futures):
            ip = futures[future]
            try:
                results[ip] = future.result()
            except Exception:
                results[ip] = None

    return results
