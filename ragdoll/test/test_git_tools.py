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
import subprocess
import tempfile
import unittest

from ragdoll.utils.git_tools import GitTools


class TestGitCreateUser(unittest.TestCase):
    """The return code must reflect the real result of the git config commands."""

    def setUp(self):
        self._tmp_dir = tempfile.mkdtemp(prefix="ragdoll-git-test-")
        self._old_cwd = os.getcwd()
        subprocess.run(["git", "init", "-q", self._tmp_dir], check=True)
        os.chdir(self._tmp_dir)

    def tearDown(self):
        os.chdir(self._old_cwd)
        shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def test_success_returns_zero_and_sets_user(self):
        git_tools = GitTools(self._tmp_dir)
        res = git_tools.git_create_user("ragdoll", "ragdoll@example.com")
        self.assertEqual(res, 0)
        name = subprocess.run(["git", "config", "user.name"], check=True,
                              capture_output=True, text=True).stdout.strip()
        email = subprocess.run(["git", "config", "user.email"], check=True,
                               capture_output=True, text=True).stdout.strip()
        self.assertEqual(name, "ragdoll")
        self.assertEqual(email, "ragdoll@example.com")

    def test_failure_outside_repository_returns_nonzero(self):
        outside = tempfile.mkdtemp(prefix="ragdoll-not-repo-")
        old_cwd = os.getcwd()
        os.chdir(outside)
        try:
            git_tools = GitTools(outside)
            res = git_tools.git_create_user("ragdoll", "ragdoll@example.com")
            self.assertEqual(res, 1)
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(outside, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
