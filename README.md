# lanscan

A small Python CLI for discovering devices on a local IPv4 LAN using ARP.

## Features

- Active LAN discovery using `arp-scan`
- Numeric IP sorting
- Displays IP, MAC address and vendor
- Shows apparently free addresses with `--all`
- JSON output
- No cloud services required

## Requirements

- Linux
- Python 3.11+
- `arp-scan`

Ubuntu/Debian:

```bash
sudo apt install arp-scan