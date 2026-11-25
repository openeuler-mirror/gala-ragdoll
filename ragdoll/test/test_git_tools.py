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
"""Regression tests for GitTools.git_create_user()."""

import os
import shutil
import tempfile
import unittest

from ragdoll.utils.git_tools import GitTools


class TestGitCreateUser(unittest.TestCase):
    """The return code must reflect the real result of the git config commands."""

    def test_success_returns_zero_and_sets_user(self):
        tmp_dir = tempfile.mkdtemp(prefix="ragdoll-git-test-")
        old_cwd = os.getcwd()
        os.chdir(tmp_dir)
        try:
            git_tools = GitTools(tmp_dir)
            self.assertEqual(git_tools.run_shell_return_code("git init -q"), 0)
            res = git_tools.git_create_user("ragdoll", "ragdoll@example.com")
            self.assertEqual(res, 0)
            name = git_tools.run_shell_return_output(
                "git config user.name").decode("utf-8").strip()
            email = git_tools.run_shell_return_output(
                "git config user.email").decode("utf-8").strip()
            self.assertEqual(name, "ragdoll")
            self.assertEqual(email, "ragdoll@example.com")
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_failure_outside_repository_returns_nonzero(self):
        tmp_dir = tempfile.mkdtemp(prefix="ragdoll-not-repo-")
        old_cwd = os.getcwd()
        os.chdir(tmp_dir)
        try:
            git_tools = GitTools(tmp_dir)
            res = git_tools.git_create_user("ragdoll", "ragdoll@example.com")
            self.assertEqual(res, 1)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
