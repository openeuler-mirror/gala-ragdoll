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
Description: unit tests for host_tools.py
"""
import os
import tempfile
import unittest
from unittest.mock import patch

from ragdoll.app.utils.host_tools import HostTools

HOST_ID = "551d02da-7d8c-4357-b88d-15dc55ee22cc"
HOST_ID_2 = "661d02da-7d8c-4357-b88d-15dc55ee33dd"
HOST_IP = "192.168.1.1"
DOMAIN = "test_domain"


class TestHostToolsProperties(unittest.TestCase):
    """Tests for HostTools properties."""

    @patch("ragdoll.app.utils.host_tools.HostTools.load_git_dir", return_value="/tmp")
    def test_target_dir_property(self, mock_load):
        """Test target_dir property getter and setter."""
        tools = HostTools()
        tools.target_dir = "/tmp/new"
        self.assertEqual(tools.target_dir, "/tmp/new")

    @patch("ragdoll.app.utils.host_tools.HostTools.load_git_dir", return_value="/tmp")
    def test_host_file_property(self, mock_load):
        """Test host_file property getter and setter."""
        tools = HostTools()
        tools.host_file = "new_hosts.txt"
        self.assertEqual(tools.host_file, "new_hosts.txt")


class TestHostToolsIsHostIdExist(unittest.TestCase):
    """Tests for HostTools.isHostIdExist method."""

    @patch("ragdoll.app.utils.host_tools.HostTools.load_git_dir", return_value="/tmp")
    def test_host_id_exists(self, mock_load):
        """Test isHostIdExist returns True when host ID found."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(f"{HOST_ID}\n{HOST_ID_2}\n")
            f.flush()
            try:
                tools = HostTools()
                self.assertTrue(tools.isHostIdExist(f.name, HOST_ID))
            finally:
                os.unlink(f.name)

    @patch("ragdoll.app.utils.host_tools.HostTools.load_git_dir", return_value="/tmp")
    def test_host_id_not_exists(self, mock_load):
        """Test isHostIdExist returns False when host ID not found."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(f"{HOST_ID}\n")
            f.flush()
            try:
                tools = HostTools()
                self.assertFalse(tools.isHostIdExist(f.name, HOST_ID_2))
            finally:
                os.unlink(f.name)

    @patch("ragdoll.app.utils.host_tools.HostTools.load_git_dir", return_value="/tmp")
    def test_nonexistent_file(self, mock_load):
        """Test isHostIdExist returns False for non-existent file."""
        tools = HostTools()
        self.assertFalse(tools.isHostIdExist("/nonexistent/file.txt", HOST_ID))


class TestHostToolsGetHostExistStatus(unittest.TestCase):
    """Tests for HostTools.getHostExistStatus method."""

    @patch("ragdoll.app.utils.host_tools.HostTools.load_git_dir", return_value="/tmp")
    def test_empty_host_list(self, mock_load):
        """Test getHostExistStatus returns None for empty list."""
        tools = HostTools()
        result = tools.getHostExistStatus(DOMAIN, [])
        self.assertEqual(result, (None, None))

    @patch("ragdoll.app.utils.host_tools.HostTools.load_git_dir", return_value="/tmp")
    def test_get_host_list(self, mock_load):
        """Test getHostList extracts host IDs from domain host list."""
        tools = HostTools()
        domain_host = [
            {"host_id": HOST_ID, "ip": HOST_IP, "ipv6": "None"},
            {"host_id": HOST_ID_2, "ip": "10.0.0.1", "ipv6": "None"},
        ]
        result = tools.getHostList(domain_host)
        self.assertEqual(result, [HOST_ID, HOST_ID_2])


if __name__ == "__main__":
    unittest.main()
