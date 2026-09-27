import ipaddress
import unittest

from lanscan.models import ArpDevice, DhcpLease
from lanscan.output import (
    JSON_SCHEMA_VERSION,
    build_json_data,
    build_json_document,
    build_summary,
    build_summary_json_document,
    free_addresses,
)


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
    def test_summary_counts_all_address_states(self):
        used = ipaddress.ip_address("192.168.1.1")
        conflict = ipaddress.ip_address("192.168.1.2")
        leased = ipaddress.ip_address("192.168.1.3")
        reserved = ipaddress.ip_address("192.168.1.4")

        hosts = {
            used: [
                ArpDevice(
                    ip=used,
                    mac="aa:bb:cc:dd:ee:01",
                    vendor="Vendor A",
                )
            ],
            conflict: [
                ArpDevice(
                    ip=conflict,
                    mac="aa:bb:cc:dd:ee:02",
                    vendor="Vendor B",
                ),
                ArpDevice(
                    ip=conflict,
                    mac="aa:bb:cc:dd:ee:03",
                    vendor="Vendor C",
                ),
            ],
        }

        leases = {
            used: DhcpLease(
                ip=used,
                lease_type="static",
                state="active",
            ),
            leased: DhcpLease(
                ip=leased,
                lease_type="dynamic",
                state="active",
            ),
            reserved: DhcpLease(
                ip=reserved,
                lease_type="static",
                state="active",
                status="offline",
            ),
        }

        summary = build_summary(
            "192.168.1.0/29",
            hosts,
            leases,
        )

        self.assertEqual(
            summary,
            {
                "network": "192.168.1.0/29",
                "total": 6,
                "occupied": 4,
                "used": 1,
                "conflicts": 1,
                "leased": 1,
                "reserved": 1,
                "free": 2,
            },
        )

    def test_summary_without_opnsense_is_arp_only(self):
        used = ipaddress.ip_address("192.168.1.1")
        hosts = {
            used: [
                ArpDevice(
                    ip=used,
                    mac="aa:bb:cc:dd:ee:ff",
                    vendor="Example Vendor",
                )
            ]
        }

        summary = build_summary("192.168.1.0/30", hosts)

        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["used"], 1)
        self.assertEqual(summary["leased"], 0)
        self.assertEqual(summary["reserved"], 0)
        self.assertEqual(summary["free"], 1)
    def test_json_document_has_schema_version_and_results(self):
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

        document = build_json_document(
            hosts,
            {ip: "host.ulnihnw.net"},
        )

        self.assertEqual(document["schema_version"], JSON_SCHEMA_VERSION)
        self.assertIn("results", document)
        self.assertEqual(document["results"][0]["ip"], "192.168.1.20")

    def test_summary_json_document_has_schema_version_and_summary(self):
        document = build_summary_json_document(
            "192.168.1.0/30",
            {},
        )

        self.assertEqual(document["schema_version"], JSON_SCHEMA_VERSION)
        self.assertEqual(
            document["summary"],
            {
                "network": "192.168.1.0/30",
                "total": 2,
                "occupied": 0,
                "used": 0,
                "conflicts": 0,
                "leased": 0,
                "reserved": 0,
                "free": 2,
            },
        )


if __name__ == "__main__":
    unittest.main()
