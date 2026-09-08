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
Description: unit tests for pam_config.py
"""
import unittest

from ragdoll.app.config_model.pam_config import PamConfig
from ragdoll.app.constant import SYNCHRONIZED, NOT_SYNCHRONIZE


class TestPamConfig(unittest.TestCase):
    """Tests for PamConfig class."""

    def setUp(self):
        self.config = PamConfig()

    def test_parse_normal(self):
        """Test parsing multiple PAM config entries."""
        res_infos = [
            {"path": "/etc/pam.d/login", "content": "auth required pam_unix.so"},
            {"path": "/etc/pam.d/sshd", "content": "auth required pam_unix.so"},
        ]
        result = PamConfig.parse_conf_to_dict(res_infos)
        self.assertEqual(result["/etc/pam.d/login"], "auth required pam_unix.so")
        self.assertEqual(result["/etc/pam.d/sshd"], "auth required pam_unix.so")
        self.assertEqual(len(result), 2)

    def test_parse_empty(self):
        """Test parsing empty input returns empty dict."""
        result = PamConfig.parse_conf_to_dict([])
        self.assertEqual(result, {})

    def test_read_conf(self):
        """Test read_conf stores config correctly."""
        res_infos = [{"path": "/etc/pam.d/test", "content": "test content"}]
        self.config.read_conf(res_infos)
        self.assertEqual(self.config.conf["/etc/pam.d/test"], "test content")

    def test_read_json(self):
        """Test read_json stores single config entry."""
        self.config.read_json("/etc/pam.d/test", "test content")
        self.assertEqual(self.config.conf["/etc/pam.d/test"], "test content")

    def test_write_conf(self):
        """Test write_conf returns content of single entry."""
        self.config.conf = {"/etc/pam.d/test": "auth required pam_unix.so"}
        written = self.config.write_conf()
        self.assertEqual(written, "auth required pam_unix.so")

    def test_write_conf_last_item(self):
        """Test write_conf returns last entry content."""
        self.config.conf = {
            "/etc/pam.d/a": "content_a",
            "/etc/pam.d/b": "content_b",
        }
        written = self.config.write_conf()
        self.assertEqual(written, "content_b")

    def test_conf_compare_equal(self):
        """Test conf_compare returns SYNCHRONIZED for equal strings."""
        c1 = "auth required pam_unix.so"
        c2 = "auth required pam_unix.so"
        self.assertEqual(PamConfig.conf_compare(c1, c2), SYNCHRONIZED)

    def test_conf_compare_different(self):
        """Test conf_compare returns NOT_SYNCHRONIZE for different strings."""
        c1 = "auth required pam_unix.so"
        c2 = "auth required pam_deny.so"
        self.assertEqual(PamConfig.conf_compare(c1, c2), NOT_SYNCHRONIZE)

    def test_conf_compare_with_whitespace(self):
        """Test conf_compare trims whitespace before comparison."""
        c1 = "  auth required pam_unix.so  "
        c2 = "auth required pam_unix.so"
        self.assertEqual(PamConfig.conf_compare(c1, c2), SYNCHRONIZED)


if __name__ == "__main__":
    unittest.main()
