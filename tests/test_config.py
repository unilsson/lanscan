import tempfile
import unittest
from pathlib import Path

from lanscan.config import ConfigError, load_opnsense_config


class ConfigTests(unittest.TestCase):
    def test_load_opnsense_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.toml"
            path.write_text(
                """
[opnsense]
url = "https://opnsense.example.net"
api_key = "example-key"
api_secret = "example-secret"
verify_tls = false
timeout = 2.5
""".strip()
                + "\n",
                encoding="utf-8",
            )

            config = load_opnsense_config(path)

        self.assertEqual(config.url, "https://opnsense.example.net")
        self.assertEqual(config.api_key, "example-key")
        self.assertEqual(config.api_secret, "example-secret")
        self.assertFalse(config.verify_tls)
        self.assertEqual(config.timeout, 2.5)

    def test_http_url_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.toml"
            path.write_text(
                """
[opnsense]
url = "http://opnsense.example.net"
api_key = "example-key"
api_secret = "example-secret"
""".strip()
                + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(ConfigError):
                load_opnsense_config(path)


if __name__ == "__main__":
    unittest.main()
