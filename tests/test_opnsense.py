import ipaddress
import unittest

from lanscan.opnsense import OpnsenseError, leases_in_network, parse_dhcp_leases


class OpnsenseTests(unittest.TestCase):
    def test_parse_active_isc_dhcp_lease(self):
        leases = parse_dhcp_leases(
            {
                "rows": [
                    {
                        "address": "192.168.1.42",
                        "hwaddr": "AA:BB:CC:DD:EE:FF",
                        "hostname": "example-host",
                        "if_descr": "LAN",
                        "state": "active",
                        "starts": "2026-09-27 03:00:00",
                        "ends": "2026-09-27 05:00:00",
                        "type": "dynamic",
                        "status": "online",
                    }
                ]
            }
        )

        ip = ipaddress.ip_address("192.168.1.42")
        self.assertIn(ip, leases)
        self.assertEqual(leases[ip].mac, "aa:bb:cc:dd:ee:ff")
        self.assertEqual(leases[ip].hostname, "example-host")
        self.assertEqual(leases[ip].interface, "LAN")
        self.assertEqual(leases[ip].lease_type, "dynamic")
        self.assertFalse(leases[ip].is_static)

    def test_parse_static_mapping(self):
        leases = parse_dhcp_leases(
            {
                "rows": [
                    {
                        "address": "192.168.1.68",
                        "type": "static",
                        "mac": "d8:eb:46:b6:c5:9d",
                        "starts": "",
                        "ends": "",
                        "hostname": "",
                        "descr": "Google Nest Ulfs rum",
                        "if_descr": "LAN",
                        "if": "lan",
                        "state": "active",
                        "status": "offline",
                        "man": "Google, Inc.",
                    }
                ]
            }
        )

        ip = ipaddress.ip_address("192.168.1.68")
        self.assertIn(ip, leases)
        self.assertTrue(leases[ip].is_static)
        self.assertEqual(leases[ip].lease_type, "static")
        self.assertEqual(leases[ip].status, "offline")
        self.assertEqual(
            leases[ip].description,
            "Google Nest Ulfs rum",
        )
        self.assertEqual(leases[ip].manufacturer, "Google, Inc.")

    def test_static_mapping_wins_over_dynamic_duplicate(self):
        leases = parse_dhcp_leases(
            {
                "rows": [
                    {
                        "address": "192.168.1.68",
                        "type": "static",
                        "mac": "d8:eb:46:b6:c5:9d",
                        "state": "active",
                        "status": "offline",
                    },
                    {
                        "address": "192.168.1.68",
                        "type": "dynamic",
                        "mac": "d8:eb:46:b6:c5:9d",
                        "state": "active",
                        "status": "online",
                    },
                ]
            }
        )

        ip = ipaddress.ip_address("192.168.1.68")
        self.assertTrue(leases[ip].is_static)
        self.assertEqual(leases[ip].status, "offline")

    def test_inactive_lease_is_ignored(self):
        leases = parse_dhcp_leases(
            {
                "rows": [
                    {
                        "address": "192.168.1.43",
                        "hwaddr": "aa:bb:cc:dd:ee:01",
                        "state": "free",
                    }
                ]
            }
        )

        self.assertEqual(leases, {})

    def test_legacy_client_hostname_field_is_supported(self):
        leases = parse_dhcp_leases(
            {
                "rows": [
                    {
                        "address": "192.168.1.44",
                        "hwaddr": "aa:bb:cc:dd:ee:02",
                        "client-hostname": "legacy-host",
                        "state": "active",
                    }
                ]
            }
        )

        ip = ipaddress.ip_address("192.168.1.44")
        self.assertEqual(leases[ip].hostname, "legacy-host")

    def test_leases_can_be_filtered_to_requested_network(self):
        leases = parse_dhcp_leases(
            {
                "rows": [
                    {"address": "192.168.1.10", "state": "active"},
                    {"address": "192.168.2.10", "state": "active"},
                ]
            }
        )

        filtered = leases_in_network("192.168.1.0/24", leases)

        self.assertEqual(
            [str(ip) for ip in filtered],
            ["192.168.1.10"],
        )

    def test_invalid_response_is_rejected(self):
        with self.assertRaises(OpnsenseError):
            parse_dhcp_leases({"unexpected": []})


if __name__ == "__main__":
    unittest.main()
