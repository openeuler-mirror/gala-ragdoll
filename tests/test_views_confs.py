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
Description: unit tests for ragdoll/app/views/confs.py
"""
import sys
import unittest
from unittest import mock

try:  # libyang is a C extension that may be absent; stub only when unavailable
    import libyang  # noqa: F401  # pylint: disable=unused-import
except ImportError:
    sys.modules["libyang"] = mock.MagicMock()

from ragdoll.app.views import confs as confs_views  # noqa: E402
from vulcanus.restful.resp.state import SUCCEED, PARAM_ERROR, NO_DATA  # noqa: E402


def call_post(cls, **params):
    """Invoke the undecorated post handler with a mock self, return (self, result)."""
    mock_self = mock.Mock()
    result = cls.post.__wrapped__(mock_self, **params)
    return mock_self, result


class TestGetTheSyncStatusOfDomain(unittest.TestCase):
    """Tests for GetTheSyncStatusOfDomain.post early branches."""

    def test_invalid_domain_returns_error(self):
        with mock.patch.object(confs_views.Format, "check_domain_param",
                               return_value=(400, "bad domain")):
            mock_self, _ = call_post(confs_views.GetTheSyncStatusOfDomain,
                                     domainName="dom", ip="1.1.1.1")
        mock_self.response.assert_called_once_with(code=400, message="bad domain")

    def test_no_manage_confs_returns_empty_host_status(self):
        with mock.patch.object(confs_views.Format, "check_domain_param",
                               return_value=(200, "ok")), \
             mock.patch.object(confs_views.Format, "get_host_id_by_ip", return_value="h1"), \
             mock.patch.object(confs_views.Format, "get_domain_conf",
                               return_value=(None, 0, [])):
            mock_self, _ = call_post(confs_views.GetTheSyncStatusOfDomain,
                                     domainName="dom", ip="1.1.1.1")
        mock_self.response.assert_called_once_with(
            code=SUCCEED, message="no domain conf",
            data={"domainName": "dom", "hostStatus": [{"hostId": "h1", "syncStatus": []}]})


class TestQueryExceptedConfs(unittest.TestCase):
    """Tests for QueryExceptedConfs.post param branch."""

    def test_empty_domain_names_returns_param_error(self):
        mock_self, _ = call_post(confs_views.QueryExceptedConfs, domainNames=[])
        mock_self.response.assert_called_once_with(
            code=PARAM_ERROR,
            message="The current domain does not exist, please create the domain first.")


class TestQuerySupportedConfs(unittest.TestCase):
    """Tests for QuerySupportedConfs.post validation branches."""

    def test_invalid_domain_returns_param_error(self):
        with mock.patch.object(confs_views.Format, "domainCheck", return_value=False):
            mock_self, _ = call_post(confs_views.QuerySupportedConfs, domainName="dom")
        mock_self.response.assert_called_once_with(
            code=PARAM_ERROR,
            message="Failed to verify the input parameter, please check the input parameters.")

    def test_domain_not_exist_returns_no_data(self):
        with mock.patch.object(confs_views.Format, "domainCheck", return_value=True), \
             mock.patch.object(confs_views.Format, "isDomainExist", return_value=False):
            mock_self, _ = call_post(confs_views.QuerySupportedConfs, domainName="dom")
        mock_self.response.assert_called_once_with(
            code=NO_DATA,
            message="The current domain does not exist, please create the domain first.")

    def test_empty_conf_files_returns_yang_list(self):
        with mock.patch.object(confs_views.Format, "domainCheck", return_value=True), \
             mock.patch.object(confs_views.Format, "isDomainExist", return_value=True), \
             mock.patch.object(confs_views.Format, "get_manageconf_by_domain",
                               return_value={"conf_files": []}):
            mock_self, _ = call_post(confs_views.QuerySupportedConfs, domainName="dom")
        _, kwargs = mock_self.response.call_args
        self.assertEqual(kwargs.get("code"), SUCCEED)
        self.assertEqual(kwargs.get("data"), confs_views.yang_conf_list)


if __name__ == "__main__":
    unittest.main()
