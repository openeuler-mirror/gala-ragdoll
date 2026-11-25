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
"""Regression tests for SshdConfig.parse_conf_to_dict()."""

import unittest

from ragdoll.config_model.sshd_config import SshdConfig


class TestSshdConfigParse(unittest.TestCase):
    """A malformed line must not discard the valid lines that follow it."""

    def test_single_token_line_does_not_truncate_the_rest(self):
        parsed = SshdConfig.parse_conf_to_dict(
            'Port 22\nbad\nPasswordAuthentication yes')
        self.assertEqual(parsed, [{'Port': '22'},
                                  {'PasswordAuthentication': 'yes'}])

    def test_padded_single_token_line_does_not_raise(self):
        parsed = SshdConfig.parse_conf_to_dict('  bad  \nPort 22\n')
        self.assertEqual(parsed, [{'Port': '22'}])

    def test_trailing_single_token_line_keeps_preceding_lines(self):
        parsed = SshdConfig.parse_conf_to_dict(
            'Port 22\nPermitRootLogin yes\nbad')
        self.assertEqual(parsed, [{'Port': '22'},
                                  {'PermitRootLogin': 'yes'}])

    def test_valid_lines_are_still_parsed(self):
        parsed = SshdConfig.parse_conf_to_dict('# comment\n\nPort 22\n')
        self.assertEqual(parsed, [{'Port': '22'}])


if __name__ == '__main__':
    unittest.main()
