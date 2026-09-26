# lanscan

A small Python CLI for discovering devices, resolving hostnames and detecting IPv4 address conflicts on a local LAN.

## Features

- Active LAN discovery using `arp-scan`
- Numeric IP sorting
- Displays IP address, status, reverse-DNS hostname, MAC address and vendor
- Reverse lookups through the system resolver/NSS
- DNS lookups run concurrently with a configurable timeout
- `--no-dns` mode for ARP-only scans
- Detects multiple MAC addresses responding for the same IP
- Shows apparently free addresses with `--all`
- Shows only apparently free addresses with `--free`
- Conflict-only mode with `--conflicts`
- Multiple ARP sweeps with `--passes`
- JSON output
- No cloud services required

## Requirements

- Linux
- Python 3.11+
- `arp-scan`
- `getent` for hostname lookups (normally provided by glibc/libc-bin)

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

Scan the local network and resolve PTR hostnames:

```bash
lanscan
```

Scan a specific subnet:

```bash
lanscan 192.168.1.0/24
```

Example output:

```text
IP               STATUS    HOSTNAME                          MAC                VENDOR
192.168.1.1      USED      opnsense.ulnihnw.net             20:7c:14:...       Qotom
192.168.1.20     USED      homeproxy.ulnihnw.net            aa:bb:cc:...       Intel
192.168.1.35     USED      -                                 11:22:33:...       Espressif
```

Disable hostname lookups:

```bash
lanscan 192.168.1.0/24 --no-dns
```

Change the per-query DNS timeout:

```bash
lanscan 192.168.1.0/24 --dns-timeout 0.5
```

`lanscan` uses the host operating system's resolver through `getent`. If the machine uses OPNsense/Unbound as its DNS server, PTR lookups therefore follow the same DNS path as other applications on that host.

Show used and apparently free addresses:

```bash
lanscan 192.168.1.0/24 --all
```

Show only apparently free addresses:

```bash
lanscan 192.168.1.0/24 --free
```

The network and broadcast addresses are excluded automatically. For example, with `192.168.1.0/24`, `--free` considers host addresses `192.168.1.1` through `192.168.1.254`.

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

Each JSON host includes a `hostname` field. It is `null` when no PTR/NSS name could be resolved.

Free-only JSON output:

```bash
lanscan 192.168.1.0/24 --free --json
```

Free addresses are emitted with `"status": "free"`, `"hostname": null` and an empty `devices` list. `--all --json` includes both used and free addresses.

Conflict-only JSON output:

```bash
lanscan 192.168.1.0/24 --conflicts --json
```

When `--conflicts` finds one or more conflicts, `lanscan` exits with status code `2`. If no conflicts are found it exits with `0`. This makes the command suitable for monitoring and automation.

## Code structure

```text
src/lanscan/
├── arp.py       # arp-scan execution and parsing
├── cli.py       # CLI argument parsing and orchestration
├── dns.py       # reverse hostname resolution
├── models.py    # shared data model
└── output.py    # text and JSON presentation
```

## Important

`FREE` means that no host responded to ARP during the scan. It does not guarantee that the address is permanently unused.

Likewise, conflict detection reports what was observed on the wire: more than one MAC address answered for the same IPv4 address during the scan passes.

A missing hostname only means that the system resolver did not return a name within the configured timeout. It does not affect ARP discovery.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Planned

- OPNsense DHCP lease integration
- OPNsense static mapping integration
- Better correlation of active, leased and reserved addresses
- Rich/TUI interface
