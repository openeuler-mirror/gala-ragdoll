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
Description: unit tests for constant.py
"""
import re
import unittest

from ragdoll.app.constant import (
    NOT_SYNCHRONIZE,
    SYNCHRONIZED,
    LIMITS_DOMAIN_RE,
    LIMITS_TYPE_VALUE,
    LIMITS_ITEM_VALUE,
    RESOLV_KEY_VALUE,
    FSTAB_COLUMN_NUM,
    PAM_FILE_PATH,
    DIRECTORY_FILE_PATH_LIST,
    PARENT_DIRECTORY,
    HOST_PATH_FILE,
    SYNC_CONFIG_YML,
    CONF_TRACE_YML,
    SYNC_LOG_PATH,
    CONF_TRACE_LOG_PATH,
    KEY_FILE_PREFIX,
    KEY_FILE_SUFFIX,
    IP_START_PATTERN,
    TIMED_TASK_CONFIG_PATH,
    yang_conf_list,
)

SYNC = "SYNCHRONIZED"
NOT_SYNC = "NOT SYNCHRONIZE"


class TestConstant(unittest.TestCase):
    """Tests for constant values."""

    def test_sync_constants(self):
        """Test synchronization status constants."""
        self.assertEqual(SYNCHRONIZED, SYNC)
        self.assertEqual(NOT_SYNCHRONIZE, NOT_SYNC)

    def test_limits_domain_regex_valid(self):
        """Test LIMITS_DOMAIN_RE matches valid domains."""
        self.assertIsNotNone(LIMITS_DOMAIN_RE.match("*"))
        self.assertIsNotNone(LIMITS_DOMAIN_RE.match("root"))
        self.assertIsNotNone(LIMITS_DOMAIN_RE.match("@group"))

    def test_limits_domain_regex_invalid(self):
        """Test LIMITS_DOMAIN_RE rejects invalid domains."""
        self.assertIsNone(LIMITS_DOMAIN_RE.match(""))
        self.assertIsNone(LIMITS_DOMAIN_RE.match("a"))

    def test_limits_type_value(self):
        """Test LIMITS_TYPE_VALUE contains expected types."""
        self.assertIn("soft", LIMITS_TYPE_VALUE)
        self.assertIn("hard", LIMITS_TYPE_VALUE)

    def test_limits_item_value(self):
        """Test LIMITS_ITEM_VALUE contains expected items."""
        self.assertIn("nofile", LIMITS_ITEM_VALUE)
        self.assertIn("core", LIMITS_ITEM_VALUE)

    def test_resolv_key_value(self):
        """Test RESOLV_KEY_VALUE contains expected keys."""
        self.assertIn("nameserver", RESOLV_KEY_VALUE)
        self.assertIn("domain", RESOLV_KEY_VALUE)
        self.assertIn("search", RESOLV_KEY_VALUE)

    def test_fstab_column_num(self):
        """Test FSTAB_COLUMN_NUM is 6."""
        self.assertEqual(FSTAB_COLUMN_NUM, 6)

    def test_pam_file_path(self):
        """Test PAM_FILE_PATH value."""
        self.assertEqual(PAM_FILE_PATH, "/etc/pam.d")

    def test_directory_file_path_list(self):
        """Test DIRECTORY_FILE_PATH_LIST contains PAM path."""
        self.assertIn(PAM_FILE_PATH, DIRECTORY_FILE_PATH_LIST)

    def test_ip_start_pattern(self):
        """Test IP_START_PATTERN matches valid IPs."""
        self.assertIsNotNone(re.match(IP_START_PATTERN, "192.168.1.1"))
        self.assertIsNotNone(re.match(IP_START_PATTERN, "10.0.0.1"))
        self.assertIsNone(re.match(IP_START_PATTERN, "abc"))

    def test_yang_conf_list(self):
        """Test yang_conf_list contains expected config paths."""
        self.assertIn("/etc/ssh/sshd_config", yang_conf_list)
        self.assertIn("/etc/hosts", yang_conf_list)
        self.assertIn("/etc/hostname", yang_conf_list)
        self.assertIsInstance(yang_conf_list, list)


if __name__ == "__main__":
    unittest.main()
