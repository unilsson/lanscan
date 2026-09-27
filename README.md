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
- Shows the complete address allocation with `--all`
- Shows only apparently free addresses with `--free`
- Summarizes address allocation with `--summary`, including JSON output for integrations
- Read-only OPNsense ISC DHCPv4 lease and static reservation correlation with `--opnsense`
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

Show a compact allocation summary:

```bash
lanscan 192.168.1.0/24 --summary --opnsense
```

Example:

```text
Network:   192.168.1.0/24
Total:     254
Occupied:  83
USED:      61
CONFLICT:  0
LEASED:    8
RESERVED:  14
FREE:      171
```

The summary counts address states, so `USED` and `CONFLICT` are separate categories and all status counts add up to `Total`. With `--opnsense`, dynamic leases and static reservations are included; without it, the summary is based on ARP observations only. Reverse DNS is skipped in summary mode because hostnames are not needed for the counts.

For machine-readable output:

```bash
lanscan 192.168.1.0/24 --summary --opnsense --json
```

Example:

```json
{
  "schema_version": 1,
  "summary": {
    "network": "192.168.1.0/24",
    "total": 254,
    "occupied": 83,
    "used": 61,
    "conflicts": 0,
    "leased": 8,
    "reserved": 14,
    "free": 171
  }
}
```

This compact JSON form is suitable for later integrations such as House Portal.

## OPNsense DHCP integration

The OPNsense integration is opt-in and read-only. OPNsense 26.7.x returns both dynamic leases and static DHCP mappings from the ISC DHCPv4 lease API, and `lanscan` correlates both.

Store credentials outside the repository in:

```text
~/.config/lanscan/config.toml
```

Example:

```toml
[opnsense]
url = "https://opnsense.example.net"
api_key = "YOUR_API_KEY"
api_secret = "YOUR_API_SECRET"
verify_tls = true
timeout = 3.0
```

The API user needs permission to read ISC DHCPv4 leases. Credentials are never passed on the command line.

If the firewall uses a certificate that the local machine does not trust, `verify_tls = false` can be used for a lab environment, but a trusted certificate is preferred.

Correlate ARP results with active DHCP leases:

```bash
lanscan 192.168.1.0/24 --opnsense
```

An address with a dynamic DHCP lease but no ARP response is shown as `LEASED`. A static DHCP mapping without an ARP response is shown as `RESERVED`.

Combine DHCP correlation with the free-address view:

```bash
lanscan 192.168.1.0/24 --free --opnsense
```

This excludes addresses that answered ARP, active dynamic DHCP leases, and static DHCP reservations.

Show the full address space including `USED`, `CONFLICT`, `LEASED`, `RESERVED` and `FREE`:

```bash
lanscan 192.168.1.0/24 --all --opnsense
```

Static mappings are discovered from the same OPNsense response as dynamic leases. Offline static reservations are therefore protected from appearing as `FREE`.

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

JSON output uses a versioned top-level envelope:

```json
{
  "schema_version": 1,
  "results": [
    {
      "ip": "192.168.1.20",
      "status": "used",
      "hostname": "host.example.net",
      "devices": []
    }
  ]
}
```

Each JSON host includes a `hostname` field. It is `null` when no PTR/NSS name could be resolved.

Free-only JSON output:

```bash
lanscan 192.168.1.0/24 --free --json
```

Free addresses are emitted with `"status": "free"`, `"hostname": null` and an empty `devices` list. `--all --json` includes both used and free addresses.

With `--opnsense --json`, dynamic lease-only addresses use `"status": "leased"` and static mappings use `"status": "reserved"`. The `lease` object includes fields such as `type`, `status`, `description` and `manufacturer` when OPNsense supplies them.

## JSON schema versioning

All machine-readable JSON output has a top-level `schema_version`. Consumers should check this value before parsing the payload.

Schema version `1` uses:

- `{"schema_version": 1, "results": [...]}` for scan, free, all and conflict JSON output.
- `{"schema_version": 1, "summary": {...}}` for `--summary --json`.

The schema version is independent of the `lanscan` package version. A future incompatible JSON structure will increment `schema_version`; compatible additions may keep the same schema version.

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
├── config.py    # local configuration outside the repository
├── dns.py       # reverse hostname resolution
├── models.py    # shared data model
├── opnsense.py  # read-only OPNsense DHCP API client
└── output.py    # text and JSON presentation
```

## Important

Without `--opnsense`, `FREE` means that no host responded to ARP during the scan.

With `--opnsense`, `FREE` means that no host responded to ARP and OPNsense returned neither an active dynamic lease nor a static DHCP reservation for the address. It still does not guarantee that the address is permanently unused outside the information visible to these data sources.

Likewise, conflict detection reports what was observed on the wire: more than one MAC address answered for the same IPv4 address during the scan passes.

A missing hostname only means that the system resolver did not return a name within the configured timeout. It does not affect ARP discovery.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Planned

- House Portal integration using summary/JSON data
- Better correlation and reporting of active, leased and reserved addresses
- Rich/TUI interface
