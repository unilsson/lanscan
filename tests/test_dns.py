import ipaddress
import subprocess
import unittest
from unittest.mock import patch

from lanscan.dns import parse_getent_output, resolve_hostname, resolve_hostnames


class DnsTests(unittest.TestCase):
    def test_parse_getent_output_returns_hostname(self):
        hostname = parse_getent_output(
            "192.168.1.20    homeproxy.ulnihnw.net homeproxy\n"
        )

        self.assertEqual(hostname, "homeproxy.ulnihnw.net")

    def test_parse_getent_output_removes_trailing_dot(self):
        hostname = parse_getent_output(
            "192.168.1.20    homeproxy.ulnihnw.net.\n"
        )

        self.assertEqual(hostname, "homeproxy.ulnihnw.net")

    @patch("lanscan.dns.subprocess.run")
    def test_resolve_hostname_returns_none_on_timeout(self, run):
        run.side_effect = subprocess.TimeoutExpired(
            cmd=["getent", "hosts", "192.168.1.20"],
            timeout=1.0,
        )

        hostname = resolve_hostname(
            ipaddress.ip_address("192.168.1.20"),
            timeout=1.0,
        )

        self.assertIsNone(hostname)

    @patch("lanscan.dns.subprocess.run")
    def test_resolve_hostname_returns_none_on_nxdomain_style_failure(self, run):
        run.return_value.returncode = 2
        run.return_value.stdout = ""

        hostname = resolve_hostname(
            ipaddress.ip_address("192.168.1.20"),
            timeout=1.0,
        )

        self.assertIsNone(hostname)

    @patch("lanscan.dns.shutil.which", return_value="/usr/bin/getent")
    @patch("lanscan.dns.resolve_hostname")
    def test_resolve_hostnames_returns_mapping(self, resolver, _which):
        ip1 = ipaddress.ip_address("192.168.1.1")
        ip2 = ipaddress.ip_address("192.168.1.20")

        resolver.side_effect = lambda ip, timeout: {
            ip1: "opnsense.ulnihnw.net",
            ip2: "homeproxy.ulnihnw.net",
        }[ip]

        result = resolve_hostnames([ip1, ip2], timeout=0.5)

        self.assertEqual(result[ip1], "opnsense.ulnihnw.net")
        self.assertEqual(result[ip2], "homeproxy.ulnihnw.net")


if __name__ == "__main__":
    unittest.main()
