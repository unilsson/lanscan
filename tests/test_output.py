import ipaddress
import unittest

from lanscan.models import ArpDevice
from lanscan.output import build_json_data


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


if __name__ == "__main__":
    unittest.main()
