import json
import unittest

from ragdoll.app.config_model.hostname_config import HostnameConfig
from ragdoll.app.constant import SYNCHRONIZED, NOT_SYNCHRONIZE


class TestHostnameConfig(unittest.TestCase):

    def setUp(self):
        self.config = HostnameConfig()

    # --- parse_conf_to_dict ---

    def test_parse_normal(self):
        conf = "myhost\n"
        result = HostnameConfig.parse_conf_to_dict(conf)
        self.assertEqual(result, ["myhost"])

    def test_parse_skips_comments(self):
        conf = "# comment\nmyhost\n; another\n"
        result = HostnameConfig.parse_conf_to_dict(conf)
        self.assertEqual(result, ["myhost"])

    def test_parse_skips_empty(self):
        conf = "\n\nmyhost\n\n"
        result = HostnameConfig.parse_conf_to_dict(conf)
        self.assertEqual(result, ["myhost"])

    def test_parse_replaces_tabs(self):
        conf = "my\thost\n"
        result = HostnameConfig.parse_conf_to_dict(conf)
        self.assertEqual(result, ["my host"])

    def test_parse_empty(self):
        result = HostnameConfig.parse_conf_to_dict("")
        self.assertEqual(result, [])

    # --- read_conf / write_conf ---

    def test_read_write_roundtrip(self):
        self.config.read_conf("myhost\n")
        written = self.config.write_conf()
        self.assertIn("myhost", written)

    # --- conf_compare ---

    def test_conf_compare_equal(self):
        c1 = json.dumps(["myhost"])
        c2 = json.dumps(["myhost"])
        self.assertEqual(self.config.conf_compare(c1, c2), SYNCHRONIZED)

    def test_conf_compare_different(self):
        c1 = json.dumps(["host1"])
        c2 = json.dumps(["host2"])
        self.assertEqual(self.config.conf_compare(c1, c2), NOT_SYNCHRONIZE)

    def test_conf_compare_empty_src(self):
        c1 = json.dumps([])
        c2 = json.dumps(["myhost"])
        self.assertEqual(self.config.conf_compare(c1, c2), NOT_SYNCHRONIZE)

    def test_conf_compare_empty_dst(self):
        c1 = json.dumps(["myhost"])
        c2 = json.dumps([])
        self.assertEqual(self.config.conf_compare(c1, c2), NOT_SYNCHRONIZE)


if __name__ == "__main__":
    unittest.main()
