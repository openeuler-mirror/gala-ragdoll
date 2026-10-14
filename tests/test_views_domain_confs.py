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
# pylint: disable=no-member
"""
Description: unit tests for ragdoll/app/views/domain_confs.py
"""
import sys
import unittest
from unittest import mock

try:  # libyang is a C extension that may be absent; stub only when unavailable
    import libyang  # noqa: F401  # pylint: disable=unused-import
except ImportError:
    sys.modules["libyang"] = mock.MagicMock()

from ragdoll.app.views import domain_confs as dc_views  # noqa: E402
from vulcanus.conf.constant import UserRoleType  # noqa: E402
from vulcanus.restful.resp.state import (  # noqa: E402
    SUCCEED, PARAM_ERROR, PERMESSION_ERROR, DATABASE_QUERY_ERROR,
)

_INVALID_DOMAIN_MSG = "Failed to verify the input parameter, please check the input parameters."


class TestGetManagementConfsInDomain(unittest.TestCase):
    """Validation / data branches of GetManagementConfsInDomain.post."""

    def test_invalid_domain(self):
        with mock.patch.object(dc_views.Format, "domainCheck", return_value=False):
            mock_self = mock.Mock()
            dc_views.GetManagementConfsInDomain.post.__wrapped__(mock_self, mock.Mock(),
                                                                 domainName="dom")
        mock_self.response.assert_called_once_with(code=PARAM_ERROR, message=_INVALID_DOMAIN_MSG)

    def test_conf_files_present(self):
        with mock.patch.object(dc_views.Format, "domainCheck", return_value=True):
            mock_self = mock.Mock()
            cb = mock.Mock()
            payload = {"domainName": "dom", "confFiles": [{"filePath": "x"}]}
            cb.get_domain_confs_by_domain.return_value = (SUCCEED, payload)
            dc_views.GetManagementConfsInDomain.post.__wrapped__(mock_self, cb, domainName="dom")
        _, kwargs = mock_self.response.call_args
        self.assertEqual(kwargs.get("data"), payload)

    def test_conf_files_empty(self):
        with mock.patch.object(dc_views.Format, "domainCheck", return_value=True):
            mock_self = mock.Mock()
            cb = mock.Mock()
            cb.get_domain_confs_by_domain.return_value = (SUCCEED, {"domainName": "dom", "confFiles": []})
            dc_views.GetManagementConfsInDomain.post.__wrapped__(mock_self, cb, domainName="dom")
        _, kwargs = mock_self.response.call_args
        self.assertEqual(kwargs.get("message"), "The file is Null in this domain")


class TestDeleteManagementConfsInDomain(unittest.TestCase):
    """Permission / validation branches of DeleteManagementConfsInDomain.delete."""

    def test_no_user_role(self):
        mock_self = self._run(None)
        mock_self.response.assert_called_once_with(
            code=DATABASE_QUERY_ERROR, message="Failed to query user permission information!")

    def test_normal_user_no_permission(self):
        mock_self = self._run(UserRoleType.NORMAL)
        mock_self.response.assert_called_once_with(
            code=PERMESSION_ERROR, message="no user permission to add domain host!")

    def test_invalid_domain(self):
        mock_self = self._run(UserRoleType.ADMINISTRATOR, return_value=False)
        mock_self.response.assert_called_once_with(code=PARAM_ERROR, message=_INVALID_DOMAIN_MSG)

    def _run(self, role, **domain_check):
        with mock.patch.object(dc_views, "cache") as mock_cache:
            mock_cache.user_role = role
            with mock.patch.object(dc_views.Format, "domainCheck", **domain_check):
                mock_self = mock.Mock()
                dc_views.DeleteManagementConfsInDomain.delete.__wrapped__(
                    mock_self, mock.Mock(), domainName="dom")
        return mock_self


if __name__ == "__main__":
    unittest.main()
