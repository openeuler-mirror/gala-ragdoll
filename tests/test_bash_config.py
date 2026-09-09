import json
import unittest

from ragdoll.app.config_model.bash_config import BashConfig
from ragdoll.app.constant import SYNCHRONIZED, NOT_SYNCHRONIZE


class TestBashConfig(unittest.TestCase):

    def setUp(self):
        self.config = BashConfig()

    # --- parse_conf_to_dict ---

    def test_parse_normal(self):
        conf = "alias ll='ls -la'\nalias gs='git status'\n"
        result = BashConfig.parse_conf_to_dict(conf)
        self.assertEqual(result, ["alias ll='ls -la'", "alias gs='git status'"])

    def test_parse_skips_empty(self):
        conf = "line1\n\n\nline2\n"
        result = BashConfig.parse_conf_to_dict(conf)
        self.assertEqual(result, ["line1", "line2"])

    def test_parse_empty_input(self):
        result = BashConfig.parse_conf_to_dict("")
        self.assertEqual(result, [])

    # --- read_conf / write_conf ---

    def test_read_write_roundtrip(self):
        conf = "alias ll='ls -la'\nalias gs='git status'\n"
        self.config.read_conf(conf)
        written = self.config.write_conf()
        self.assertIn("alias ll='ls -la'", written)
        self.assertIn("alias gs='git status'", written)

    def test_read_empty(self):
        self.config.read_conf("  \n  \n")
        self.assertEqual(self.config.conf, [])

    # --- conf_compare ---

    def test_conf_compare_equal(self):
        c1 = json.dumps(["alias ll='ls -la'"])
        c2 = json.dumps(["alias ll='ls -la'"])
        self.assertEqual(BashConfig.conf_compare(c1, c2), SYNCHRONIZED)

    def test_conf_compare_different(self):
        c1 = json.dumps(["alias ll='ls -la'"])
        c2 = json.dumps(["alias ll='ls -l'"])
        self.assertEqual(BashConfig.conf_compare(c1, c2), NOT_SYNCHRONIZE)

    def test_conf_compare_missing_item(self):
        c1 = json.dumps(["alias ll='ls -la'", "alias gs='git status'"])
        c2 = json.dumps(["alias ll='ls -la'"])
        self.assertEqual(BashConfig.conf_compare(c1, c2), NOT_SYNCHRONIZE)


if __name__ == "__main__":
    unittest.main()
