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
Description: unit tests for git_tools.py
"""
import os
import unittest
from unittest.mock import patch, MagicMock

from ragdoll.app.utils.git_tools import GitTools

TARGET_DIR = "/tmp/test_git_repo"
USERNAME = "testuser"
USEREMAIL = "test@example.com"


class TestGitToolsInit(unittest.TestCase):
    """Tests for GitTools initialization."""

    @patch("ragdoll.app.utils.git_tools.GitTools.load_git_dir", return_value=TARGET_DIR)
    def test_init_with_target_dir(self, mock_load):
        """Test GitTools init with explicit target_dir."""
        tools = GitTools(target_dir=TARGET_DIR)
        self.assertEqual(tools._target_dir, TARGET_DIR)

    @patch("ragdoll.app.utils.git_tools.GitTools.load_git_dir", return_value=TARGET_DIR)
    def test_init_without_target_dir(self, mock_load):
        """Test GitTools init uses load_git_dir."""
        tools = GitTools()
        mock_load.assert_called()

    @patch("ragdoll.app.utils.git_tools.GitTools.load_git_dir", return_value=TARGET_DIR)
    def test_target_dir_property(self, mock_load):
        """Test target_dir property getter and setter."""
        tools = GitTools(target_dir=TARGET_DIR)
        tools.target_dir = "/tmp/new_dir"
        self.assertEqual(tools.target_dir, "/tmp/new_dir")

    @patch("ragdoll.app.utils.git_tools.GitTools.load_git_dir", return_value=TARGET_DIR)
    def test_make_git_message_empty(self, mock_load):
        """Test makeGitMessage returns error for empty message."""
        tools = GitTools(target_dir=TARGET_DIR)
        result = tools.makeGitMessage("/tmp/test", "")
        self.assertEqual(result, "the logMessage is null")

    @patch("ragdoll.app.utils.git_tools.GitTools.load_git_dir", return_value=TARGET_DIR)
    @patch("ragdoll.app.utils.git_tools.GitTools.run_shell_return_output")
    @patch("ragdoll.app.utils.git_tools.os.chdir")
    @patch("ragdoll.app.utils.git_tools.os.getcwd", return_value="/tmp")
    def test_make_git_message_single_commit(self, mock_cwd, mock_chdir, mock_run, mock_load):
        """Test makeGitMessage parses single commit."""
        log_msg = (
            "commit abc123\n"
            "Author: Test User <test@example.com>\n"
            "Date:   Mon Jan 1 12:00:00 2024\n"
            "\n"
            "    Initial commit\n"
        )
        tools = GitTools(target_dir=TARGET_DIR)
        with patch("ragdoll.app.utils.git_tools.Format") as mock_format:
            mock_format.get_file_content_by_read.return_value = "file content"
            result = tools.makeGitMessage("/tmp/test", log_msg)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["changeId"], "abc123")


if __name__ == "__main__":
    unittest.main()
