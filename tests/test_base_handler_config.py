# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2021-2022. All rights reserved.
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
Description: unit tests for base_handler_config.py
"""
import json
import unittest

from ragdoll.app.config_model.base_handler_config import BaseHandlerConfig
from ragdoll.app.constant import SYNCHRONIZED, NOT_SYNCHRONIZE

FAKE_PATH = "/tmp/fake"
KEY = "key"
KEY_A = "a"
KEY_B = "b"
VAL_1 = "1"
VAL_2 = "2"


class TestBaseHandlerConfig(unittest.TestCase):
    """Tests for BaseHandlerConfig class."""

    def setUp(self):
        self.config = BaseHandlerConfig()

    def test_read_json_list(self):
        """Test read_json with a JSON list."""
        data = [{KEY: "val1"}, {KEY: "val2"}]
        self.config.read_json(FAKE_PATH, json.dumps(data))
        self.assertEqual(len(self.config.conf), 2)
        self.assertEqual(self.config.conf[0][KEY], "val1")

    def test_read_json_empty_list(self):
        """Test read_json with an empty JSON list."""
        self.config.read_json(FAKE_PATH, "[]")
        self.assertEqual(self.config.conf, [])

    def test_conf_compare_equal(self):
        """Test conf_compare returns SYNCHRONIZED when lists are equal."""
        c1 = json.dumps([{KEY_A: VAL_1}, {KEY_B: VAL_2}])
        c2 = json.dumps([{KEY_A: VAL_1}, {KEY_B: VAL_2}])
        self.assertEqual(self.config.conf_compare(c1, c2), SYNCHRONIZED)

    def test_conf_compare_different(self):
        """Test conf_compare returns NOT_SYNCHRONIZE when values differ."""
        c1 = json.dumps([{KEY_A: VAL_1}])
        c2 = json.dumps([{KEY_A: VAL_2}])
        self.assertEqual(self.config.conf_compare(c1, c2), NOT_SYNCHRONIZE)

    def test_conf_compare_missing_item(self):
        """Test conf_compare returns NOT_SYNCHRONIZE when item is missing."""
        c1 = json.dumps([{KEY_A: VAL_1}, {KEY_B: VAL_2}])
        c2 = json.dumps([{KEY_A: VAL_1}])
        self.assertEqual(self.config.conf_compare(c1, c2), NOT_SYNCHRONIZE)

    def test_init_defaults(self):
        """Test BaseHandlerConfig initializes with empty lists."""
        cfg = BaseHandlerConfig()
        self.assertEqual(cfg.conf, [])
        self.assertEqual(cfg.yang, [])


if __name__ == "__main__":
    unittest.main()
