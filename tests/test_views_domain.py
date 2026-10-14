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
Description: unit tests for ragdoll/app/views/domain.py
"""
import sys
import unittest
from unittest import mock

try:  # libyang is a C extension that may be absent; stub only when unavailable
    import libyang  # noqa: F401
except ImportError:
    sys.modules["libyang"] = mock.MagicMock()

from ragdoll.app.views import domain as domain_views  # noqa: E402
from vulcanus.conf.constant import UserRoleType  # noqa: E402
from vulcanus.restful.resp.state import (  # noqa: E402
    PARAM_ERROR, PERMESSION_ERROR, DATABASE_QUERY_ERROR,
)


def call_handler(cls, role, method, **params):
    """Run an undecorated view handler with the module's cache replaced by a mock.

    ``user_role`` is a property on the real cache, so the whole ``cache`` object is
    swapped for a Mock whose ``user_role`` we control.
    """
    with mock.patch.object(domain_views, "cache") as mock_cache:
        mock_cache.user_role = role
        mock_self = mock.Mock()
        if method == "post":
            cls.post.__wrapped__(mock_self, mock.Mock(), **params)
        else:
            cls.delete.__wrapped__(mock_self, mock.Mock(), **params)
    return mock_self


class TestCreateDomain(unittest.TestCase):
    """Permission-check branches of CreateDomain.post."""

    def test_no_user_role(self):
        mock_self = call_handler(domain_views.CreateDomain, None, "post", domainName="dom")
        mock_self.response.assert_called_once_with(
            code=DATABASE_QUERY_ERROR, message="Failed to query user permission information!")

    def test_normal_user_has_no_permission(self):
        mock_self = call_handler(domain_views.CreateDomain, UserRoleType.NORMAL, "post",
                                 domainName="dom")
        mock_self.response.assert_called_once_with(
            code=PERMESSION_ERROR, message="no user permission to create domain!")


class TestDeleteDomain(unittest.TestCase):
    """Permission / empty-name branches of DeleteDomain.delete."""

    def test_no_user_role(self):
        mock_self = call_handler(domain_views.DeleteDomain, None, "delete", domainName="dom")
        mock_self.response.assert_called_once_with(
            code=DATABASE_QUERY_ERROR, message="Failed to query user permission information!")

    def test_normal_user_has_no_permission(self):
        mock_self = call_handler(domain_views.DeleteDomain, UserRoleType.NORMAL, "delete",
                                 domainName="dom")
        mock_self.response.assert_called_once_with(
            code=PERMESSION_ERROR, message="no user permission to delete domain!")

    def test_empty_domain_name(self):
        mock_self = call_handler(domain_views.DeleteDomain, UserRoleType.ADMINISTRATOR,
                                 "delete", domainName="")
        mock_self.response.assert_called_once_with(
            code=PARAM_ERROR, message="The entered domain is empty")


class TestQueryDomain(unittest.TestCase):
    """Permission-check branch of QueryDomain.post."""

    def test_no_user_role(self):
        mock_self = call_handler(domain_views.QueryDomain, None, "post")
        mock_self.response.assert_called_once_with(
            code=DATABASE_QUERY_ERROR, message="Failed to query user permission information!")


if __name__ == "__main__":
    unittest.main()
