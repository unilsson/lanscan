# lanscan

A small Python CLI for discovering devices and detecting IPv4 address conflicts on a local LAN using ARP.

## Features

- Active LAN discovery using `arp-scan`
- Numeric IP sorting
- Displays IP address, MAC address and vendor
- Detects multiple MAC addresses responding for the same IP
- Shows apparently free addresses with `--all`
- Conflict-only mode with `--conflicts`
- Multiple ARP sweeps with `--passes`
- JSON output
- No cloud services required

## Requirements

- Linux
- Python 3.11+
- `arp-scan`

Ubuntu/Debian:

```bash
sudo apt install arp-scan
```

## Development installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

Scan the local network:

```bash
lanscan
```

Scan a specific subnet:

```bash
lanscan 192.168.1.0/24
```

Show used and apparently free addresses:

```bash
lanscan 192.168.1.0/24 --all
```

Show only detected IP conflicts:

```bash
lanscan 192.168.1.0/24 --conflicts
```

Conflict detection performs three ARP sweeps by default so that devices that do not answer in the same sweep can still be correlated. Override this with:

```bash
lanscan 192.168.1.0/24 --conflicts --passes 5
```

JSON output:

```bash
lanscan 192.168.1.0/24 --json
```

Conflict-only JSON output:

```bash
lanscan 192.168.1.0/24 --conflicts --json
```

When `--conflicts` finds one or more conflicts, `lanscan` exits with status code `2`. If no conflicts are found it exits with `0`. This makes the command suitable for monitoring and automation.

## Important

`FREE` means that no host responded to ARP during the scan. It does not guarantee that the address is permanently unused.

Likewise, conflict detection reports what was observed on the wire: more than one MAC address answered for the same IPv4 address during the scan passes.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Planned

- OPNsense DHCP lease integration
- OPNsense static mapping integration
- Hostnames and DNS data
- Better correlation of active, leased and reserved addresses
- Rich/TUI interface
