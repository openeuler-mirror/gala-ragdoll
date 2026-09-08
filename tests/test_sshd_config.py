import json
import unittest

from ragdoll.app.config_model.sshd_config import SshdConfig
from ragdoll.app.constant import SYNCHRONIZED, NOT_SYNCHRONIZE


class TestSshdConfig(unittest.TestCase):

    def setUp(self):
        self.config = SshdConfig()

    # --- parse_conf_to_dict ---

    def test_parse_normal(self):
        conf = "Port 22\nPermitRootLogin yes"
        result = SshdConfig.parse_conf_to_dict(conf)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], {"Port": "22"})
        self.assertEqual(result[1], {"PermitRootLogin": "yes"})

    def test_parse_skips_comments_and_semicolons(self):
        conf = "# comment\n; another\nPort 22\n"
        result = SshdConfig.parse_conf_to_dict(conf)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], {"Port": "22"})

    def test_parse_skips_empty_lines(self):
        conf = "\n\nPort 22\n\n"
        result = SshdConfig.parse_conf_to_dict(conf)
        self.assertEqual(len(result), 1)

    def test_parse_single_field_returns_empty(self):
        conf = "InvalidOnly"
        result = SshdConfig.parse_conf_to_dict(conf)
        self.assertEqual(result, [])

    def test_parse_empty(self):
        result = SshdConfig.parse_conf_to_dict("")
        self.assertEqual(result, [])

    # --- read_conf ---

    def test_read_conf(self):
        conf = "Port 22\nPermitRootLogin yes"
        self.config.read_conf(conf)
        self.assertEqual(len(self.config.conf), 2)

    def test_read_conf_empty_not_stored(self):
        self.config.read_conf("")
        self.assertEqual(self.config.conf, [])

    # --- read_json ---

    def test_read_json(self):
        data = [{"Port": "22"}]
        self.config.read_json("/tmp/fake", json.dumps(data))
        self.assertEqual(len(self.config.conf), 1)
        self.assertEqual(self.config.conf[0]["Port"], "22")

    # --- write_conf ---

    def test_write_conf_space_separator(self):
        self.config.conf = [{"Port": "22"}, {"PermitRootLogin": "yes"}]
        spacer_info = {"openEuler-sshd_config": ""}
        written = self.config.write_conf(spacer_info)
        self.assertIn("Port 22", written)
        self.assertIn("PermitRootLogin yes", written)

    # --- conf_compare ---

    def test_conf_compare_equal(self):
        c1 = json.dumps([{"Port": "22"}])
        c2 = json.dumps([{"Port": "22"}])
        self.assertEqual(SshdConfig.conf_compare(c1, c2), SYNCHRONIZED)

    def test_conf_compare_different(self):
        c1 = json.dumps([{"Port": "22"}])
        c2 = json.dumps([{"Port": "2222"}])
        self.assertEqual(SshdConfig.conf_compare(c1, c2), NOT_SYNCHRONIZE)

    def test_conf_compare_missing_item(self):
        c1 = json.dumps([{"Port": "22"}, {"PermitRootLogin": "yes"}])
        c2 = json.dumps([{"Port": "22"}])
        self.assertEqual(SshdConfig.conf_compare(c1, c2), NOT_SYNCHRONIZE)

    # --- init ---

    def test_init_defaults(self):
        cfg = SshdConfig()
        self.assertEqual(cfg.conf, [])
        self.assertEqual(cfg.yang, [])


if __name__ == "__main__":
    unittest.main()
