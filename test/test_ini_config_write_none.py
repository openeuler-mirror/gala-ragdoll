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
"""Regression tests for IniConfig.write_conf()."""

import unittest

from ragdoll.config_model.ini_config import IniConfig


class TestIniConfigWriteNone(unittest.TestCase):
    """Null option values must be skipped, not repeated from the previous option."""

    def test_none_value_does_not_repeat_previous_option(self):
        config = IniConfig()
        config.conf = {'main': {'first': '1', 'absent': None}}
        content = config.write_conf()
        self.assertEqual(content.count('first = 1'), 1)
        self.assertNotIn('absent', content)

    def test_none_value_as_first_option_does_not_raise(self):
        config = IniConfig()
        config.conf = {'main': {'absent': None, 'second': '2'}}
        content = config.write_conf()
        self.assertIn('second = 2', content)
        self.assertNotIn('absent', content)


if __name__ == '__main__':
    unittest.main()
