import ipaddress
import unittest
from collections import defaultdict

from lanscan.cli import build_parser, find_conflicts, parse_arp_scan_output


class ParseArpScanOutputTests(unittest.TestCase):
    def test_parses_host(self):
        hosts = parse_arp_scan_output(
            "192.168.1.10\taa:bb:cc:dd:ee:ff\tExample Vendor\n"
        )
        ip = ipaddress.ip_address("192.168.1.10")

        self.assertEqual(hosts[ip][0].mac, "aa:bb:cc:dd:ee:ff")
        self.assertEqual(hosts[ip][0].vendor, "Example Vendor")

    def test_duplicate_reply_from_same_mac_is_ignored(self):
        output = (
            "192.168.1.10\taa:bb:cc:dd:ee:ff\tExample Vendor\n"
            "192.168.1.10\taa:bb:cc:dd:ee:ff\tExample Vendor\n"
        )

        hosts = parse_arp_scan_output(output)
        ip = ipaddress.ip_address("192.168.1.10")

        self.assertEqual(len(hosts[ip]), 1)

    def test_two_macs_on_same_ip_are_reported_as_conflict(self):
        output = (
            "192.168.1.10\taa:bb:cc:dd:ee:ff\tVendor A\n"
            "192.168.1.10\t11:22:33:44:55:66\tVendor B\n"
        )

        hosts = parse_arp_scan_output(output)
        conflicts = find_conflicts(hosts)
        ip = ipaddress.ip_address("192.168.1.10")

        self.assertIn(ip, conflicts)
        self.assertEqual(len(conflicts[ip]), 2)

    def test_conflict_can_be_detected_across_multiple_passes(self):
        hosts = defaultdict(list)

        parse_arp_scan_output(
            "192.168.1.20\taa:bb:cc:dd:ee:ff\tVendor A\n",
            hosts,
        )
        parse_arp_scan_output(
            "192.168.1.20\t11:22:33:44:55:66\tVendor B\n",
            hosts,
        )

        conflicts = find_conflicts(hosts)
        ip = ipaddress.ip_address("192.168.1.20")

        self.assertEqual(len(conflicts[ip]), 2)

    def test_ip_addresses_sort_numerically(self):
        hosts = parse_arp_scan_output(
            "192.168.1.100\taa:bb:cc:dd:ee:01\tA\n"
            "192.168.1.9\taa:bb:cc:dd:ee:02\tB\n"
            "192.168.1.10\taa:bb:cc:dd:ee:03\tC\n"
        )

        self.assertEqual(
            [str(ip) for ip in sorted(hosts)],
            ["192.168.1.9", "192.168.1.10", "192.168.1.100"],
        )

    def test_free_is_a_view_option(self):
        args = build_parser().parse_args(["192.168.1.0/24", "--free"])

        self.assertTrue(args.free)
        self.assertFalse(args.all)
        self.assertFalse(args.conflicts)

    def test_free_and_all_are_mutually_exclusive(self):
        with self.assertRaises(SystemExit):
            build_parser().parse_args(
                ["192.168.1.0/24", "--free", "--all"]
            )

    def test_opnsense_flag_is_available(self):
        args = build_parser().parse_args(
            ["192.168.1.0/24", "--opnsense"]
        )

        self.assertTrue(args.opnsense)


if __name__ == "__main__":
    unittest.main()
