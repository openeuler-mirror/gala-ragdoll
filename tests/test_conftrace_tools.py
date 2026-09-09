# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2021-2022. All rights reserved.
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
Description: unit tests for conftrace_tools.py
"""
import unittest
from unittest.mock import patch, MagicMock

from vulcanus.restful.resp.state import SUCCEED, SERVER_ERROR
from ragdoll.app.utils.conftrace_tools import ConfTraceTools

HOST_IP = "192.168.1.1"
SSH_PORT = "22"
HOST_KEY = f"{HOST_IP}_{SSH_PORT}"
ACTION_START = "start"
ACTION_STOP = "stop"


class TestConfTraceToolsParseResult(unittest.TestCase):
    """Tests for ConfTraceTools.parse_result static method."""

    @patch("ragdoll.app.utils.conftrace_tools.os.remove")
    @patch("ragdoll.app.utils.conftrace_tools.os.path.exists", return_value=True)
    @patch("ragdoll.app.utils.conftrace_tools.glob.glob", return_value=[])
    def test_parse_result_success(self, mock_glob, mock_exists, mock_remove):
        """Test parse_result with successful ansible output."""
        result = f"{HOST_KEY}: unreachable=0 failed=0 changed=0"
        host_ip_trace_result = {}
        code_num, code_string = ConfTraceTools.parse_result(
            ACTION_START, result, host_ip_trace_result, "/tmp/test_hosts"
        )
        self.assertEqual(code_num, SUCCEED)
        self.assertIn(ACTION_START, code_string)

    @patch("ragdoll.app.utils.conftrace_tools.os.remove")
    @patch("ragdoll.app.utils.conftrace_tools.os.path.exists", return_value=True)
    @patch("ragdoll.app.utils.conftrace_tools.glob.glob", return_value=[])
    def test_parse_result_no_unreachable(self, mock_glob, mock_exists, mock_remove):
        """Test parse_result with no unreachable lines returns SERVER_ERROR."""
        result = "some random output"
        host_ip_trace_result = {}
        code_num, _ = ConfTraceTools.parse_result(
            ACTION_START, result, host_ip_trace_result, "/tmp/test_hosts"
        )
        self.assertEqual(code_num, SERVER_ERROR)

    @patch("ragdoll.app.utils.conftrace_tools.os.remove")
    @patch("ragdoll.app.utils.conftrace_tools.os.path.exists", return_value=True)
    @patch("ragdoll.app.utils.conftrace_tools.glob.glob", return_value=[])
    def test_parse_result_failure(self, mock_glob, mock_exists, mock_remove):
        """Test parse_result with unreachable != 0."""
        result = f"{HOST_KEY}: unreachable=1 failed=0 changed=0"
        host_ip_trace_result = {}
        ConfTraceTools.parse_result(
            ACTION_START, result, host_ip_trace_result, "/tmp/test_hosts"
        )
        self.assertFalse(host_ip_trace_result.get(HOST_KEY, True))

    @patch("ragdoll.app.utils.conftrace_tools.os.remove")
    @patch("ragdoll.app.utils.conftrace_tools.os.path.exists", return_value=True)
    @patch("ragdoll.app.utils.conftrace_tools.glob.glob", return_value=[])
    def test_parse_result_cleans_files(self, mock_glob, mock_exists, mock_remove):
        """Test parse_result removes temp files."""
        result = f"{HOST_KEY}: unreachable=0 failed=0"
        host_ip_trace_result = {}
        ConfTraceTools.parse_result(
            ACTION_STOP, result, host_ip_trace_result, "/tmp/test_hosts"
        )
        mock_remove.assert_called()


if __name__ == "__main__":
    unittest.main()
