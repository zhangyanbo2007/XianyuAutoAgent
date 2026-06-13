"""Regression tests for pipeline configuration."""

import unittest
from urllib.parse import urlparse

import config


class MimoConfigTest(unittest.TestCase):
    def test_api_base_url_uses_working_mimo_host(self):
        parsed = urlparse(config.API_BASE_URL)

        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "token-plan-cn.xiaomimimo.com")
        self.assertEqual(parsed.path.rstrip("/"), "/v1")


if __name__ == "__main__":
    unittest.main()
