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
Description: unit tests for prepare.py
"""
import unittest
from unittest.mock import patch, MagicMock

from ragdoll.app.utils.prepare import Prepare

TARGET_DIR = "/tmp/test_prepare"
USERNAME = "testuser"
USEREMAIL = "test@example.com"


class TestPrepare(unittest.TestCase):
    """Tests for Prepare class."""

    def test_init(self):
        """Test Prepare initializes with target_dir."""
        prepare = Prepare(TARGET_DIR)
        self.assertEqual(prepare.target_dir, TARGET_DIR)

    def test_target_dir_property(self):
        """Test target_dir property getter and setter."""
        prepare = Prepare(TARGET_DIR)
        prepare.target_dir = "/tmp/new_dir"
        self.assertEqual(prepare.target_dir, "/tmp/new_dir")

    @patch("ragdoll.app.utils.prepare.GitTools")
    @patch("ragdoll.app.utils.prepare.os.path.exists", return_value=False)
    @patch("ragdoll.app.utils.prepare.os.mkdir")
    def test_mkdir_git_warehouse_creates_dir(self, mock_mkdir, mock_exists, mock_git):
        """Test mkdir_git_warehose creates directory when not exists."""
        mock_tools = MagicMock()
        mock_tools.run_shell_return_code.return_value = 0
        mock_git.return_value = mock_tools
        prepare = Prepare(TARGET_DIR)
        with patch.object(prepare, "git_init", return_value=True):
            result = prepare.mkdir_git_warehose(USERNAME, USEREMAIL)
            self.assertTrue(result)

    @patch("ragdoll.app.utils.prepare.os.path.exists", return_value=True)
    def test_mkdir_git_warehouse_existing_dir(self, mock_exists):
        """Test mkdir_git_warehose with existing directory."""
        prepare = Prepare(TARGET_DIR)
        with patch.object(prepare, "git_init", return_value=True):
            result = prepare.mkdir_git_warehose(USERNAME, USEREMAIL)
            self.assertTrue(result)

    @patch("ragdoll.app.utils.prepare.GitTools")
    @patch("ragdoll.app.utils.prepare.os.chdir")
    @patch("ragdoll.app.utils.prepare.os.getcwd", return_value="/tmp")
    def test_git_init_success(self, mock_cwd, mock_chdir, mock_git_cls):
        """Test git_init returns True on success."""
        mock_tools = MagicMock()
        mock_tools.gitInit.return_value = 0
        mock_tools.git_create_user.return_value = 0
        mock_git_cls.return_value = mock_tools
        prepare = Prepare(TARGET_DIR)
        result = prepare.git_init(USERNAME, USEREMAIL)
        self.assertTrue(result)

    @patch("ragdoll.app.utils.prepare.GitTools")
    @patch("ragdoll.app.utils.prepare.os.chdir")
    @patch("ragdoll.app.utils.prepare.os.getcwd", return_value="/tmp")
    def test_git_init_failure(self, mock_cwd, mock_chdir, mock_git_cls):
        """Test git_init returns False on failure."""
        mock_tools = MagicMock()
        mock_tools.gitInit.return_value = 1
        mock_tools.git_create_user.return_value = 0
        mock_git_cls.return_value = mock_tools
        prepare = Prepare(TARGET_DIR)
        result = prepare.git_init(USERNAME, USEREMAIL)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
