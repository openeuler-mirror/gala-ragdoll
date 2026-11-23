#!/usr/bin/python3
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
"""Regression tests for BaseConfig.conf_compare()."""

import json
import unittest

from ragdoll.config_model.base_config import BaseConfig
from ragdoll.const.conf_handler_const import NOT_SYNCHRONIZE, SYNCHRONIZED


class TestBaseConfigCompare(unittest.TestCase):
    """Configuration comparison must cover every key and its value."""

    def test_extra_key_in_dst_is_not_synchronized(self):
        config = BaseConfig()
        result = config.conf_compare(
            json.dumps({'a': '1'}), json.dumps({'a': '1', 'b': '2'}))
        self.assertEqual(result, NOT_SYNCHRONIZE)

    def test_missing_key_in_dst_is_not_synchronized(self):
        config = BaseConfig()
        result = config.conf_compare(
            json.dumps({'a': '1', 'b': '2'}), json.dumps({'a': '1'}))
        self.assertEqual(result, NOT_SYNCHRONIZE)

    def test_different_value_for_same_key_is_not_synchronized(self):
        config = BaseConfig()
        result = config.conf_compare(
            json.dumps({'a': '1'}), json.dumps({'a': '2'}))
        self.assertEqual(result, NOT_SYNCHRONIZE)

    def test_same_content_in_different_order_is_synchronized(self):
        config = BaseConfig()
        result = config.conf_compare(
            json.dumps({'b': '2', 'a': '1'}), json.dumps({'a': '1', 'b': '2'}))
        self.assertEqual(result, SYNCHRONIZED)


if __name__ == '__main__':
    unittest.main()
