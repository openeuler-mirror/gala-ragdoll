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

IP_V4 = "127.0.0.1"
HOSTNAME_LOCAL = "localhost"
IP_V4_ALT = "192.168.1.10"
HOSTNAME_ALT = "myhost"


class TestHostsConfig(unittest.TestCase):
    """Tests for HostsConfig class."""

    def setUp(self):
        self.config = HostsConfig()

    def test_read_conf_ipv4(self):
        """Test parsing IPv4 addresses via read_conf."""
        conf = f"{IP_V4} {HOSTNAME_LOCAL}\n{IP_V4_ALT} {HOSTNAME_ALT}"
        self.config.read_conf(conf)
        self.assertEqual(self.config.conf[IP_V4], HOSTNAME_LOCAL)
        self.assertEqual(self.config.conf[IP_V4_ALT], HOSTNAME_ALT)

    def test_read_conf_ipv6(self):
        """Test parsing IPv6 addresses via read_conf."""
        conf = f"::1 {HOSTNAME_LOCAL}"
        self.config.read_conf(conf)
        self.assertIn("::1", self.config.conf)

    def test_read_conf_multiple_aliases(self):
        """Test parsing multiple host aliases via read_conf."""
        conf = f"{IP_V4} host1 host2 host3"
        self.config.read_conf(conf)
        self.assertEqual(self.config.conf[IP_V4], "host1 host2 host3")

    def test_read_conf_skips_comments_and_empty(self):
        """Test that comments and empty lines are skipped via read_conf."""
        conf = f"# comment\n\n{IP_V4} {HOSTNAME_LOCAL}\n"
        self.config.read_conf(conf)
        self.assertEqual(len(self.config.conf), 1)

    def test_read_conf_error_invalid_ip(self):
        """Test invalid IP address does not store config."""
        conf = "not-an-ip hostname"
        self.config.read_conf(conf)
        self.assertEqual(self.config.conf, {})

    def test_read_conf_error_single_field(self):
        """Test single field without hostname does not store config."""
        conf = IP_V4
        self.config.read_conf(conf)
        self.assertEqual(self.config.conf, {})

    def test_read_write_roundtrip(self):
        """Test read_conf and write_conf produce consistent output."""
        conf = f"{IP_V4} {HOSTNAME_LOCAL}"
        self.config.read_conf(conf)
        self.assertEqual(self.config.conf[IP_V4], HOSTNAME_LOCAL)
        written = self.config.write_conf()
        self.assertIn(IP_V4, written)
        self.assertIn(HOSTNAME_LOCAL, written)

    def test_conf_compare_equal(self):
        """Test conf_compare returns SYNCHRONIZED for equal configs."""
        c1 = json.dumps({IP_V4: HOSTNAME_LOCAL})
        c2 = json.dumps({IP_V4: HOSTNAME_LOCAL})
        self.assertEqual(HostsConfig.conf_compare(c1, c2), SYNCHRONIZED)

    def test_conf_compare_different_value(self):
        """Test conf_compare returns NOT_SYNCHRONIZE for different values."""
        c1 = json.dumps({IP_V4: "host1"})
        c2 = json.dumps({IP_V4: "host2"})
        self.assertEqual(HostsConfig.conf_compare(c1, c2), NOT_SYNCHRONIZE)

    def test_conf_compare_missing_key(self):
        """Test conf_compare returns NOT_SYNCHRONIZE for missing key."""
        c1 = json.dumps({IP_V4: HOSTNAME_LOCAL, "192.168.1.1": HOSTNAME_ALT})
        c2 = json.dumps({IP_V4: HOSTNAME_LOCAL})
        self.assertEqual(HostsConfig.conf_compare(c1, c2), NOT_SYNCHRONIZE)


if __name__ == "__main__":
    unittest.main()
