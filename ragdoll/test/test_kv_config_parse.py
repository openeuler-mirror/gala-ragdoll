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
"""Regression tests for KvConfig.parse_conf_to_dict()."""

import unittest

from ragdoll.config_model.kv_config import KvConfig


class TestKvConfigParse(unittest.TestCase):
    """A malformed line must not discard the valid lines that follow it."""

    def test_single_token_line_does_not_truncate_the_rest(self):
        parsed = KvConfig.parse_conf_to_dict(
            'a 1\nbad\nc 3', {'test-kv': ''}, 'test-kv')
        self.assertEqual(parsed, [{'a': '1'}, {'c': '3'}])

    def test_padded_single_token_line_does_not_raise(self):
        parsed = KvConfig.parse_conf_to_dict(
            '  bad  \na 1\n', {'test-kv': ''}, 'test-kv')
        self.assertEqual(parsed, [{'a': '1'}])

    def test_line_without_separator_does_not_raise_in_equal_mode(self):
        parsed = KvConfig.parse_conf_to_dict(
            'a=1\nbad\nc=3', {'test-kv': '='}, 'test-kv')
        self.assertEqual(parsed, [{'a': '1'}, {'c': '3'}])


if __name__ == '__main__':
    unittest.main()
