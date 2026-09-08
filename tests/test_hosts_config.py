# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2021-2021. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN 'AS IS' BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************/
"""
Description: unit tests for hosts_config.py
"""
import json
import unittest

from ragdoll.app.config_model.hosts_config import HostsConfig
from ragdoll.app.constant import SYNCHRONIZED, NOT_SYNCHRONIZE


class TestHostsConfig(unittest.TestCase):
    """Tests for HostsConfig class."""

    def setUp(self):
        self.config = HostsConfig()

    def test_parse_ipv4(self):
        """Test parsing IPv4 addresses."""
        conf = "127.0.0.1 localhost\n192.168.1.10 myhost"
        error, result = HostsConfig._parse_network_conf_to_dict(conf)
        self.assertFalse(error)
        self.assertEqual(result["127.0.0.1"], "localhost")
        self.assertEqual(result["192.168.1.10"], "myhost")

    def test_parse_ipv6(self):
        """Test parsing IPv6 addresses."""
        conf = "::1 localhost"
        error, result = HostsConfig._parse_network_conf_to_dict(conf)
        self.assertFalse(error)
        self.assertIn("::1", result)

    def test_parse_multiple_aliases(self):
        """Test parsing multiple host aliases."""
        conf = "127.0.0.1 host1 host2 host3"
        error, result = HostsConfig._parse_network_conf_to_dict(conf)
        self.assertFalse(error)
        self.assertEqual(result["127.0.0.1"], "host1 host2 host3")

    def test_parse_skips_comments_and_empty(self):
        """Test that comments and empty lines are skipped."""
        conf = "# comment\n\n127.0.0.1 localhost\n"
        error, result = HostsConfig._parse_network_conf_to_dict(conf)
        self.assertFalse(error)
        self.assertEqual(len(result), 1)

    def test_parse_error_invalid_ip(self):
        """Test error returned for invalid IP address."""
        conf = "not-an-ip hostname"
        error, result = HostsConfig._parse_network_conf_to_dict(conf)
        self.assertTrue(error)

    def test_parse_error_single_field(self):
        """Test error returned for single field without hostname."""
        conf = "127.0.0.1"
        error, result = HostsConfig._parse_network_conf_to_dict(conf)
        self.assertTrue(error)

    def test_read_write_roundtrip(self):
        """Test read_conf and write_conf produce consistent output."""
        conf = "127.0.0.1 localhost"
        self.config.read_conf(conf)
        self.assertEqual(self.config.conf["127.0.0.1"], "localhost")
        written = self.config.write_conf()
        self.assertIn("127.0.0.1", written)
        self.assertIn("localhost", written)

    def test_conf_compare_equal(self):
        """Test conf_compare returns SYNCHRONIZED for equal configs."""
        c1 = json.dumps({"127.0.0.1": "localhost"})
        c2 = json.dumps({"127.0.0.1": "localhost"})
        self.assertEqual(HostsConfig.conf_compare(c1, c2), SYNCHRONIZED)

    def test_conf_compare_different_value(self):
        """Test conf_compare returns NOT_SYNCHRONIZE for different values."""
        c1 = json.dumps({"127.0.0.1": "host1"})
        c2 = json.dumps({"127.0.0.1": "host2"})
        self.assertEqual(HostsConfig.conf_compare(c1, c2), NOT_SYNCHRONIZE)

    def test_conf_compare_missing_key(self):
        """Test conf_compare returns NOT_SYNCHRONIZE for missing key."""
        c1 = json.dumps({"127.0.0.1": "localhost", "192.168.1.1": "myhost"})
        c2 = json.dumps({"127.0.0.1": "localhost"})
        self.assertEqual(HostsConfig.conf_compare(c1, c2), NOT_SYNCHRONIZE)


if __name__ == "__main__":
    unittest.main()
