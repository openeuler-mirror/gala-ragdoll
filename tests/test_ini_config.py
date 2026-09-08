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
Description: unit tests for ini_config.py
"""
import unittest

from collections import OrderedDict
from ragdoll.app.config_model.ini_config import IniConfig

SECTION1 = "section1"
SEC = "sec"
KEY = "key"
KEY1 = "key1"
KEY2 = "key2"
VALUE1 = "value1"
VALUE2 = "value2"


class TestIniConfig(unittest.TestCase):
    """Tests for IniConfig class."""

    def setUp(self):
        self.config = IniConfig()

    def test_read_conf_normal(self):
        """Test parsing standard INI section with key-value pairs."""
        conf = f"[{SECTION1}]\n{KEY1} = {VALUE1}\n{KEY2} = {VALUE2}\n"
        self.config.read_conf(conf)
        self.assertIn(SECTION1, self.config.conf)
        self.assertEqual(self.config.conf[SECTION1][KEY1], VALUE1)
        self.assertEqual(self.config.conf[SECTION1][KEY2], VALUE2)

    def test_read_conf_colon_separator(self):
        """Test parsing INI with colon separator."""
        self.config.yang = OrderedDict()
        self.config.yang[SEC] = OrderedDict()
        self.config.yang[SEC][KEY] = None
        conf = f"[{SEC}]\n{KEY}: value\n"
        self.config.read_conf(conf)
        self.assertEqual(self.config.conf[SEC][KEY], "value")

    def test_read_conf_skips_comments_and_empty(self):
        """Test that comments and empty lines are skipped."""
        self.config.yang = OrderedDict()
        self.config.yang[SEC] = OrderedDict()
        self.config.yang[SEC][KEY] = None
        conf = f"# comment\n[{SEC}]\n; another\n{KEY} = val\n\n"
        self.config.read_conf(conf)
        self.assertIn(SEC, self.config.conf)
        self.assertEqual(self.config.conf[SEC][KEY], "val")

    def test_read_conf_duplicate_section_merges(self):
        """Test duplicate section names are merged."""
        self.config.yang = OrderedDict()
        self.config.yang[SEC] = OrderedDict()
        self.config.yang[SEC]["k1"] = None
        self.config.yang[SEC]["k2"] = None
        conf = f"[{SEC}]\nk1 = v1\n[{SEC}]\nk2 = v2\n"
        self.config.read_conf(conf)
        self.assertEqual(self.config.conf[SEC]["k1"], "v1")
        self.assertEqual(self.config.conf[SEC]["k2"], "v2")

    def test_read_conf_empty(self):
        """Test parsing empty string results in empty conf."""
        self.config.read_conf("")
        self.assertEqual(dict(self.config.conf), {})

    def test_write_conf(self):
        """Test write_conf generates correct INI output."""
        self.config.conf = OrderedDict()
        self.config.conf[SECTION1] = OrderedDict()
        self.config.conf[SECTION1]["__name__"] = SECTION1
        self.config.conf[SECTION1][KEY1] = VALUE1
        written = self.config.write_conf()
        self.assertIn(f"[{SECTION1}]", written)
        self.assertIn(f"{KEY1} = {VALUE1}", written)


if __name__ == "__main__":
    unittest.main()
