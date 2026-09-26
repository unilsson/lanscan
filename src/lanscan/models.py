from dataclasses import dataclass
from ipaddress import IPv4Address


@dataclass(frozen=True, slots=True)
class ArpDevice:
    """One device observed answering ARP for an IPv4 address."""

    ip: IPv4Address
    mac: str
    vendor: str

    def as_dict(self):
        return {
            "ip": str(self.ip),
            "mac": self.mac,
            "vendor": self.vendor,
        }
