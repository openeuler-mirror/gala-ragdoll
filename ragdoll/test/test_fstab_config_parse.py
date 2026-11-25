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
"""Regression tests for FstabConfig.parse_conf_to_dict()."""

import unittest

from ragdoll.config_model.fstab_config import FstabConfig

VALID_LINE = '/dev/sda1 / ext4 defaults 0 1'


class TestFstabConfigParse(unittest.TestCase):
    """A malformed line must not discard the valid lines that follow it."""

    def test_malformed_line_does_not_truncate_the_rest(self):
        error_conf, parsed = FstabConfig.parse_conf_to_dict(
            VALID_LINE + '\nbad line\n/dev/sda2 /boot ext4 defaults 0 2')
        self.assertFalse(error_conf)
        self.assertEqual(
            parsed,
            [['/dev/sda1', '/', 'ext4', 'defaults', '0', '1'],
             ['/dev/sda2', '/boot', 'ext4', 'defaults', '0', '2']])

    def test_trailing_malformed_line_keeps_preceding_lines(self):
        error_conf, parsed = FstabConfig.parse_conf_to_dict(
            VALID_LINE + '\nbad line')
        self.assertFalse(error_conf)
        self.assertEqual(
            parsed, [['/dev/sda1', '/', 'ext4', 'defaults', '0', '1']])

    def test_valid_lines_are_still_parsed(self):
        error_conf, parsed = FstabConfig.parse_conf_to_dict(
            '# comment\n\n' + VALID_LINE + '\n')
        self.assertFalse(error_conf)
        self.assertEqual(
            parsed, [['/dev/sda1', '/', 'ext4', 'defaults', '0', '1']])

    def test_only_malformed_lines_yields_empty_result(self):
        error_conf, parsed = FstabConfig.parse_conf_to_dict('bad line\n')
        self.assertFalse(error_conf)
        self.assertEqual(parsed, [])


if __name__ == '__main__':
    unittest.main()
