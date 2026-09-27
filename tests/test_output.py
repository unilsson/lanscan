import ipaddress
import unittest

from lanscan.models import ArpDevice, DhcpLease
from lanscan.output import build_json_data, free_addresses


class OutputTests(unittest.TestCase):
    def test_json_contains_hostname(self):
        ip = ipaddress.ip_address("192.168.1.20")
        hosts = {
            ip: [
                ArpDevice(
                    ip=ip,
                    mac="aa:bb:cc:dd:ee:ff",
                    vendor="Example Vendor",
                )
            ]
        }

        data = build_json_data(
            hosts,
            {ip: "homeproxy.ulnihnw.net"},
        )

        self.assertEqual(data[0]["hostname"], "homeproxy.ulnihnw.net")
        self.assertEqual(data[0]["status"], "used")
        self.assertEqual(
            data[0]["devices"][0]["mac"],
            "aa:bb:cc:dd:ee:ff",
        )

    def test_free_addresses_excludes_used_network_and_broadcast(self):
        used = ipaddress.ip_address("192.168.1.2")
        hosts = {
            used: [
                ArpDevice(
                    ip=used,
                    mac="aa:bb:cc:dd:ee:ff",
                    vendor="Example Vendor",
                )
            ]
        }

        free = free_addresses("192.168.1.0/30", hosts)

        self.assertEqual(
            [str(ip) for ip in free],
            ["192.168.1.1"],
        )

    def test_free_addresses_excludes_active_dhcp_lease(self):
        leased = ipaddress.ip_address("192.168.1.1")
        used = ipaddress.ip_address("192.168.1.2")
        hosts = {
            used: [
                ArpDevice(
                    ip=used,
                    mac="aa:bb:cc:dd:ee:ff",
                    vendor="Example Vendor",
                )
            ]
        }
        leases = {
            leased: DhcpLease(
                ip=leased,
                mac="11:22:33:44:55:66",
                hostname="sleeping-host",
                state="active",
                lease_type="dynamic",
            )
        }

        free = free_addresses("192.168.1.0/30", hosts, leases)

        self.assertEqual(free, [])

    def test_free_addresses_excludes_static_reservation(self):
        reserved = ipaddress.ip_address("192.168.1.1")
        hosts = {}
        leases = {
            reserved: DhcpLease(
                ip=reserved,
                mac="11:22:33:44:55:66",
                state="active",
                lease_type="static",
                status="offline",
            )
        }

        free = free_addresses("192.168.1.0/30", hosts, leases)

        self.assertEqual(
            [str(ip) for ip in free],
            ["192.168.1.2"],
        )

    def test_free_only_json_contains_only_free_hosts(self):
        used = ipaddress.ip_address("192.168.1.2")
        hosts = {
            used: [
                ArpDevice(
                    ip=used,
                    mac="aa:bb:cc:dd:ee:ff",
                    vendor="Example Vendor",
                )
            ]
        }

        data = build_json_data(
            hosts,
            {},
            network="192.168.1.0/30",
            free_only=True,
        )

        self.assertEqual(
            data,
            [
                {
                    "ip": "192.168.1.1",
                    "status": "free",
                    "hostname": None,
                    "devices": [],
                }
            ],
        )

    def test_all_json_contains_used_and_free_hosts(self):
        used = ipaddress.ip_address("192.168.1.2")
        hosts = {
            used: [
                ArpDevice(
                    ip=used,
                    mac="aa:bb:cc:dd:ee:ff",
                    vendor="Example Vendor",
                )
            ]
        }

        data = build_json_data(
            hosts,
            {used: "host.ulnihnw.net"},
            network="192.168.1.0/30",
            include_free=True,
        )

        self.assertEqual([row["status"] for row in data], ["free", "used"])
        self.assertEqual(data[1]["hostname"], "host.ulnihnw.net")

    def test_json_contains_lease_only_address(self):
        leased = ipaddress.ip_address("192.168.1.42")
        leases = {
            leased: DhcpLease(
                ip=leased,
                mac="aa:bb:cc:dd:ee:ff",
                hostname="sleeping-host",
                state="active",
                lease_type="dynamic",
            )
        }

        data = build_json_data(
            {},
            {},
            leases=leases,
        )

        self.assertEqual(data[0]["status"], "leased")
        self.assertEqual(data[0]["hostname"], "sleeping-host")
        self.assertEqual(data[0]["devices"], [])
        self.assertEqual(data[0]["lease"]["mac"], "aa:bb:cc:dd:ee:ff")

    def test_json_contains_static_reservation(self):
        reserved = ipaddress.ip_address("192.168.1.68")
        leases = {
            reserved: DhcpLease(
                ip=reserved,
                mac="d8:eb:46:b6:c5:9d",
                state="active",
                lease_type="static",
                status="offline",
                description="Google Nest Ulfs rum",
                manufacturer="Google, Inc.",
            )
        }

        data = build_json_data(
            {},
            {},
            leases=leases,
        )

        self.assertEqual(data[0]["status"], "reserved")
        self.assertEqual(data[0]["lease"]["type"], "static")
        self.assertEqual(data[0]["lease"]["status"], "offline")
        self.assertEqual(
            data[0]["lease"]["description"],
            "Google Nest Ulfs rum",
        )


if __name__ == "__main__":
    unittest.main()
