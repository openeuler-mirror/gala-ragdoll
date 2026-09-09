import json
import unittest

from ragdoll.app.config_model.ssh_config import SshConfig
from ragdoll.app.constant import SYNCHRONIZED, NOT_SYNCHRONIZE


class TestSshConfig(unittest.TestCase):

    def setUp(self):
        self.config = SshConfig()

    # --- parse_conf_to_dict ---

    def test_parse_simple_kv(self):
        conf = "Port 22\nProtocol 2"
        error, result = self.config.parse_conf_to_dict(conf)
        self.assertFalse(error)
        self.assertEqual(result["Port"], "22")
        self.assertEqual(result["Protocol"], "2")

    def test_parse_with_block(self):
        conf = "Host bastion\n\tHostName 10.0.0.1\n\tUser admin"
        error, result = self.config.parse_conf_to_dict(conf)
        self.assertFalse(error)
        self.assertIsInstance(result["Host bastion"], list)
        self.assertEqual(result["Host bastion"][0], {"HostName": "10.0.0.1"})

    def test_parse_skips_comments_and_empty(self):
        conf = "# comment\n\nPort 22\n"
        error, result = self.config.parse_conf_to_dict(conf)
        self.assertFalse(error)
        self.assertEqual(result["Port"], "22")

    def test_parse_error_first_line_indented(self):
        conf = "  indented\nPort 22"
        error, result = self.config.parse_conf_to_dict(conf)
        self.assertTrue(error)

    def test_parse_line_to_dict_normal(self):
        error, key, value = SshConfig.parse_line_to_dict("Port 22")
        self.assertFalse(error)
        self.assertEqual(key, "Port")
        self.assertEqual(value, "22")

    def test_parse_line_to_dict_single_field(self):
        error, key, value = SshConfig.parse_line_to_dict("InvalidOnly")
        self.assertTrue(error)
        self.assertEqual(key, "InvalidOnly")

    def test_parse_line_to_dict_multiple_values(self):
        error, key, value = SshConfig.parse_line_to_dict("Host * -X")
        self.assertFalse(error)
        self.assertEqual(key, "Host")
        self.assertEqual(value, "* -X")

    # --- read_conf ---

    def test_read_conf(self):
        conf = "Port 22\nProtocol 2"
        self.config.read_conf(conf)
        self.assertEqual(self.config.conf["Port"], "22")

    def test_read_conf_error_not_stored(self):
        conf = "  indented"
        self.config.read_conf(conf)
        self.assertEqual(self.config.conf, {})

    # --- write_conf ---

    def test_write_conf_simple_kv(self):
        self.config.conf = {"Port": "22", "Protocol": "2"}
        written = self.config.write_conf()
        self.assertIn("Port 22", written)
        self.assertIn("Protocol 2", written)

    def test_write_conf_with_block(self):
        self.config.conf = {"Host bastion": [{"HostName": "10.0.0.1"}, {"User": "admin"}]}
        written = self.config.write_conf()
        self.assertIn("Host bastion", written)
        self.assertIn("HostName 10.0.0.1", written)

    # --- conf_compare ---

    def test_conf_compare_equal(self):
        c1 = json.dumps({"Port": "22"})
        c2 = json.dumps({"Port": "22"})
        self.assertEqual(SshConfig.conf_compare(c1, c2), SYNCHRONIZED)

    def test_conf_compare_different_value(self):
        c1 = json.dumps({"Port": "22"})
        c2 = json.dumps({"Port": "2222"})
        self.assertEqual(SshConfig.conf_compare(c1, c2), NOT_SYNCHRONIZE)

    def test_conf_compare_missing_key(self):
        c1 = json.dumps({"Port": "22", "Protocol": "2"})
        c2 = json.dumps({"Port": "22"})
        self.assertEqual(SshConfig.conf_compare(c1, c2), NOT_SYNCHRONIZE)

    def test_conf_compare_list_value(self):
        c1 = json.dumps({"Host bastion": [{"HostName": "10.0.0.1"}]})
        c2 = json.dumps({"Host bastion": [{"HostName": "10.0.0.1"}]})
        self.assertEqual(SshConfig.conf_compare(c1, c2), SYNCHRONIZED)


if __name__ == "__main__":
    unittest.main()
