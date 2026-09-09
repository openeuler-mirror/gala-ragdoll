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
Description: unit tests for conf_tools.py
"""
import unittest

from ragdoll.app.utils.conf_tools import ConfTools, SyncRes

CONF_PATH = "path"
CONF_VALUE = "expectedValue"


class TestSyncRes(unittest.TestCase):
    """Tests for SyncRes enum."""

    def test_success_value(self):
        """Test SyncRes.SUCCESS has correct value."""
        self.assertEqual(SyncRes.SUCCESS.value, "SUCCESS")

    def test_failed_value(self):
        """Test SyncRes.FAILED has correct value."""
        self.assertEqual(SyncRes.FAILED.value, "FAILED")


class TestConfTools(unittest.TestCase):
    """Tests for ConfTools class."""

    def setUp(self):
        self.tools = ConfTools()

    def test_switch_perm_read(self):
        """Test switch_perm returns 4 for read."""
        self.assertEqual(self.tools.switch_perm("r"), 4)

    def test_switch_perm_write(self):
        """Test switch_perm returns 2 for write."""
        self.assertEqual(self.tools.switch_perm("w"), 2)

    def test_switch_perm_execute(self):
        """Test switch_perm returns 1 for execute."""
        self.assertEqual(self.tools.switch_perm("x"), 1)

    def test_switch_perm_other(self):
        """Test switch_perm returns 0 for other."""
        self.assertEqual(self.tools.switch_perm("-"), 0)
        self.assertEqual(self.tools.switch_perm("s"), 0)

    def test_get_xpath_in_manager_confs(self):
        """Test getXpathInManagerConfs extracts paths."""
        confs = [
            {CONF_PATH: "/etc/hosts"},
            {CONF_PATH: "/etc/hostname"},
        ]
        result = self.tools.getXpathInManagerConfs(confs)
        self.assertEqual(result, ["/etc/hosts", "/etc/hostname"])

    def test_get_xpath_in_manager_confs_empty(self):
        """Test getXpathInManagerConfs with empty list."""
        result = self.tools.getXpathInManagerConfs([])
        self.assertEqual(result, [])

    def test_list_to_dict(self):
        """Test listToDict converts conf list to nested dict."""
        mana_confs = [
            {CONF_PATH: "/etc/hosts", CONF_VALUE: " 127.0.0.1 localhost  "},
        ]
        result = self.tools.listToDict(mana_confs)
        self.assertIn("etc", result)

    def test_management_confs_property(self):
        """Test managementConfs property getter and setter."""
        self.assertEqual(self.tools.managementConfs, [])
        new_confs = [{"path": "/test"}]
        self.tools.managementConfs = new_confs
        self.assertEqual(self.tools.managementConfs, new_confs)

    def test_target_dir_property(self):
        """Test target_dir property getter and setter."""
        self.tools.target_dir = "/tmp/test"
        self.assertEqual(self.tools.target_dir, "/tmp/test")

    def test_add_feature_in_real_conf(self):
        """Test addFeatureInRealConf adds feature to real config."""
        real_conf = {"/etc/hosts": "content"}
        feature_list = ["hosts", "/etc/hosts", "hosts_file"]
        result = self.tools.addFeatureInRealConf(real_conf, feature_list, "test_domain")
        self.assertIn("hosts_file", result)


if __name__ == "__main__":
    unittest.main()
