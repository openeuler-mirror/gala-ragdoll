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
Description: unit tests for base_config.py
"""
import json
import unittest

from ragdoll.app.config_model.base_config import BaseConfig
from ragdoll.app.constant import SYNCHRONIZED, NOT_SYNCHRONIZE


class TestBaseConfig(unittest.TestCase):
    """Tests for BaseConfig class."""

    def setUp(self):
        self.config = BaseConfig()

    def test_read_json_basic(self):
        """Test read_json with basic key-value pairs."""
        data = {"key1": "value1", "key2": "value2"}
        self.config.read_json("/tmp/fake", json.dumps(data))
        self.assertEqual(self.config.conf["key1"], "value1")
        self.assertEqual(self.config.conf["key2"], "value2")

    def test_read_json_empty(self):
        """Test read_json with empty JSON object."""
        self.config.read_json("/tmp/fake", "{}")
        self.assertEqual(self.config.conf, {})

    def test_read_json_nested(self):
        """Test read_json with nested JSON structure."""
        data = {"section": {"opt": "val"}}
        self.config.read_json("/tmp/fake", json.dumps(data))
        self.assertEqual(self.config.conf["section"]["opt"], "val")

    def test_conf_compare_equal(self):
        """Test conf_compare returns SYNCHRONIZED when configs are equal."""
        c1 = json.dumps({"a": "1", "b": "2"})
        c2 = json.dumps({"b": "2", "a": "1"})
        self.assertEqual(self.config.conf_compare(c1, c2), SYNCHRONIZED)

    def test_conf_compare_different(self):
        """Test conf_compare returns NOT_SYNCHRONIZE when values differ."""
        c1 = json.dumps({"a": "1"})
        c2 = json.dumps({"a": "2"})
        self.assertEqual(self.config.conf_compare(c1, c2), NOT_SYNCHRONIZE)

    def test_conf_compare_extra_key(self):
        """Test conf_compare returns NOT_SYNCHRONIZE when keys differ."""
        c1 = json.dumps({"a": "1", "b": "2"})
        c2 = json.dumps({"a": "1"})
        self.assertEqual(self.config.conf_compare(c1, c2), NOT_SYNCHRONIZE)

    def test_conf_compare_empty(self):
        """Test conf_compare with empty JSON objects."""
        self.assertEqual(self.config.conf_compare("{}", "{}"), SYNCHRONIZED)

    def test_conf_compare_type_coercion(self):
        """Test conf_compare handles int vs string comparison."""
        c1 = json.dumps({"a": 1})
        c2 = json.dumps({"a": "1"})
        self.assertEqual(self.config.conf_compare(c1, c2), SYNCHRONIZED)

    def test_init_defaults(self):
        """Test BaseConfig initializes with empty dicts."""
        cfg = BaseConfig()
        self.assertEqual(dict(cfg.conf), {})
        self.assertEqual(dict(cfg.yang), {})


if __name__ == "__main__":
    unittest.main()
