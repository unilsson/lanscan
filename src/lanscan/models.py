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


@dataclass(frozen=True, slots=True)
class DhcpLease:
    """One active DHCPv4 lease or static mapping reported by OPNsense."""

    ip: IPv4Address
    mac: str | None = None
    hostname: str | None = None
    interface: str | None = None
    state: str | None = None
    starts: str | None = None
    ends: str | None = None
    lease_type: str | None = None
    status: str | None = None
    description: str | None = None
    manufacturer: str | None = None

    @property
    def is_static(self) -> bool:
        return (self.lease_type or "").lower() == "static"

    def as_dict(self):
        return {
            "ip": str(self.ip),
            "mac": self.mac,
            "hostname": self.hostname,
            "interface": self.interface,
            "state": self.state,
            "starts": self.starts,
            "ends": self.ends,
            "type": self.lease_type,
            "status": self.status,
            "description": self.description,
            "manufacturer": self.manufacturer,
        }
