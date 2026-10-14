# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2022-2022. All rights reserved.
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
Description: unit tests for ragdoll/app/core/ssh.py
"""
import socket
import unittest
from unittest import mock

import paramiko

from ragdoll.app.core.model import ClientConnectArgs
from ragdoll.app.core.ssh import (
    SSH,
    execute_command_and_parse_its_result,
    execute_command_sftp_result,
    generate_key,
)
from vulcanus.restful.resp import state


def _args(pkey="FAKE-PRIVATE-KEY"):
    """Build a ClientConnectArgs used as SSH connect arguments."""
    return ClientConnectArgs(
        host_ip="1.2.3.4", ssh_port=22, ssh_user="root", pkey=pkey, timeout=5
    )


class TestGenerateKey(unittest.TestCase):
    """Tests for the generate_key helper."""

    def test_returns_private_and_public_pair(self):
        """generate_key produces an RSA private key and an ssh-rsa public key."""
        private_key, public_key = generate_key()
        self.assertIn("RSA PRIVATE KEY", private_key)
        self.assertTrue(public_key.startswith("ssh-rsa "))


class TestExecuteCommandAndParse(unittest.TestCase):
    """Tests for execute_command_and_parse_its_result branches."""

    def test_missing_pkey_returns_authentication_error(self):
        """Without a pkey the host ip is reported and no SSH is attempted."""
        status, msg = execute_command_and_parse_its_result(_args(pkey=None), "ls")
        self.assertEqual(status, state.SSH_AUTHENTICATION_ERROR)
        self.assertIn("1.2.3.4", msg)

    @mock.patch("paramiko.RSAKey.from_private_key")
    @mock.patch("ragdoll.app.core.ssh.SSH")
    def test_success_returns_stdout(self, mock_ssh, _):
        """Exit status 0 maps to SUCCEED and the command stdout."""
        mock_ssh.return_value.execute_command.return_value = (0, "out-data", "ignored")
        status, result = execute_command_and_parse_its_result(_args(), "ls")
        self.assertEqual(status, state.SUCCEED)
        self.assertEqual(result, "out-data")
        mock_ssh.return_value.close.assert_called_once()

    @mock.patch("paramiko.RSAKey.from_private_key")
    @mock.patch("ragdoll.app.core.ssh.SSH")
    def test_nonzero_exit_returns_error(self, mock_ssh, _):
        """A non-zero exit status maps to EXECUTE_COMMAND_ERROR with stderr."""
        mock_ssh.return_value.execute_command.return_value = (1, "out", "some-error")
        status, result = execute_command_and_parse_its_result(_args(), "ls")
        self.assertEqual(status, state.EXECUTE_COMMAND_ERROR)
        self.assertEqual(result, "some-error")

    @mock.patch("paramiko.RSAKey.from_private_key")
    def test_socket_error(self, _):
        """A socket.error during connect maps to SSH_CONNECTION_ERROR."""
        with mock.patch("ragdoll.app.core.ssh.SSH", side_effect=socket.error("boom")):
            status, msg = execute_command_and_parse_its_result(_args(), "ls")
        self.assertEqual(status, state.SSH_CONNECTION_ERROR)
        self.assertEqual(msg, "SSH.Connection.Error")

    @mock.patch("paramiko.RSAKey.from_private_key")
    def test_ssh_exception(self, _):
        """An SSHException during connect maps to SSH_AUTHENTICATION_ERROR."""
        with mock.patch(
            "ragdoll.app.core.ssh.SSH",
            side_effect=paramiko.ssh_exception.SSHException("bad"),
        ):
            status, msg = execute_command_and_parse_its_result(_args(), "ls")
        self.assertEqual(status, state.SSH_AUTHENTICATION_ERROR)
        self.assertEqual(msg, "SSH.Authentication.Error")


class TestExecuteSftp(unittest.TestCase):
    """Tests for execute_command_sftp_result branches."""

    def test_missing_pkey(self):
        """Without a pkey the host ip is reported before any transfer."""
        status, msg = execute_command_sftp_result(
            _args(pkey=None), local_path="l", remote_path="r"
        )
        self.assertEqual(status, state.SSH_AUTHENTICATION_ERROR)
        self.assertIn("1.2.3.4", msg)

    @mock.patch("paramiko.RSAKey.from_private_key")
    def test_success(self, _):
        """A completed put maps to SUCCEED and closes both clients."""
        with mock.patch("ragdoll.app.core.ssh.SSH") as mock_ssh:
            sftp = mock_ssh.return_value.client.return_value.open_sftp.return_value
            sftp.put.return_value = None
            status = execute_command_sftp_result(_args(), local_path="l", remote_path="r")
        self.assertEqual(status, state.SUCCEED)
        sftp.put.assert_called_once_with("l", "r")
        sftp.close.assert_called_once()
        mock_ssh.return_value.close.assert_called_once()

    @mock.patch("paramiko.RSAKey.from_private_key")
    def test_generic_exception(self, _):
        """An unexpected transfer error maps to SSH_AUTHENTICATION_ERROR."""
        with mock.patch("ragdoll.app.core.ssh.SSH") as mock_ssh:
            mock_ssh.return_value.client.return_value.open_sftp.return_value.put.side_effect = (
                RuntimeError("nope")
            )
            status, msg = execute_command_sftp_result(
                _args(), local_path="l", remote_path="r"
            )
        self.assertEqual(status, state.SSH_AUTHENTICATION_ERROR)
        self.assertEqual(msg, "SSH.Authentication.Error")


class TestSSHClient(unittest.TestCase):
    """Tests for the SSH class execute_command / close paths."""

    @mock.patch("paramiko.client.SSHClient")
    def test_execute_command_parses_output(self, mock_client_cls):
        """execute_command reads exit status, stdout and stderr from the channel."""
        ssh = SSH(ip="1.2.3.4", username="root", port=22, pkey="KEY")
        setattr(ssh, "_client", mock_client_cls.return_value)
        channel = mock_client_cls.return_value.get_transport.return_value.open_session.return_value
        channel.recv_exit_status.return_value = 0
        channel.makefile.return_value.read.return_value = b"stdout"
        channel.makefile_stderr.return_value.read.return_value = b"stderr"

        status, out, err = ssh.execute_command("ls", timeout=1)

        self.assertEqual(status, 0)
        self.assertEqual(out, "stdout")
        self.assertEqual(err, "stderr")
        channel.set_combine_stderr.assert_called_once_with(False)

    def test_close_delegates_to_client(self):
        """close() closes the underlying paramiko client."""
        ssh = SSH.__new__(SSH)
        client = mock.Mock()
        setattr(ssh, "_client", client)
        ssh.close()
        client.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
