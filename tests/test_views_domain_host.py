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
Description: unit tests for ragdoll/app/views/domain_host.py
"""
import sys
import unittest
from unittest import mock

try:  # libyang is a C extension that may be absent; stub only when unavailable
    import libyang  # noqa: F401
except ImportError:
    sys.modules["libyang"] = mock.MagicMock()

from ragdoll.app.views import domain_host as dh_views  # noqa: E402
from vulcanus.restful.resp.state import SUCCEED, NO_DATA  # noqa: E402


class TestGetHostByDomainName(unittest.TestCase):
    """Code-branch behavior of GetHostByDomainName.post."""

    def test_error_code_returns_unknown_problem(self):
        cb = mock.Mock()
        cb.get_domain_host_by_domain.return_value = (500, [])
        mock_self = mock.Mock()
        dh_views.GetHostByDomainName.post.__wrapped__(mock_self, cb, domainName="dom")
        mock_self.response.assert_called_once_with(code=500, message="Some unknown problems.")

    def test_success_returns_data(self):
        cb = mock.Mock()
        cb.get_domain_host_by_domain.return_value = (SUCCEED, [{"hostId": "h1"}])
        mock_self = mock.Mock()
        dh_views.GetHostByDomainName.post.__wrapped__(mock_self, cb, domainName="dom")
        mock_self.response.assert_called_once_with(
            code=SUCCEED, message="Get host info in the domain successfully",
            data=[{"hostId": "h1"}])


class TestGetNonexistentDomainHost(unittest.TestCase):
    """Early-return / filter branches of GetNonexistentDomainHost.post."""

    def test_no_hosts_in_cluster(self):
        with mock.patch.object(dh_views.Format, "get_cluster_all_host", return_value=[]):
            mock_self = mock.Mock()
            dh_views.GetNonexistentDomainHost.post.__wrapped__(mock_self, mock.Mock(), clusterId="c1")
        mock_self.response.assert_called_once_with(
            code=NO_DATA, message="No hosts are available in the current cluster")

    def test_no_domain_in_cluster(self):
        with mock.patch.object(dh_views.Format, "get_cluster_all_host",
                               return_value=[{"host_id": "h1"}]), \
             mock.patch.object(dh_views.Format, "get_cluster_domain", return_value=[]):
            mock_self = mock.Mock()
            dh_views.GetNonexistentDomainHost.post.__wrapped__(mock_self, mock.Mock(), clusterId="c1")
        mock_self.response.assert_called_once_with(
            code=NO_DATA, message="No domain in the current cluster")

    def test_no_added_hosts_returns_all(self):
        with mock.patch.object(dh_views.Format, "get_cluster_all_host",
                               return_value=[{"host_id": "h1"}]), \
             mock.patch.object(dh_views.Format, "get_cluster_domain", return_value=["d1"]):
            cb = mock.Mock()
            cb.get_domain_host_by_domain_id_list.return_value = (SUCCEED, [])
            mock_self = mock.Mock()
            dh_views.GetNonexistentDomainHost.post.__wrapped__(mock_self, cb, clusterId="c1")
        _, kwargs = mock_self.response.call_args
        self.assertEqual(kwargs["data"], [{"host_id": "h1"}])

    def test_filters_existing_hosts(self):
        cluster_hosts = [{"host_id": "h1"}, {"host_id": "h2"}]
        with mock.patch.object(dh_views.Format, "get_cluster_all_host", return_value=cluster_hosts), \
             mock.patch.object(dh_views.Format, "get_cluster_domain", return_value=["d1"]):
            cb = mock.Mock()
            cb.get_domain_host_by_domain_id_list.return_value = (SUCCEED, [{"hostId": "h1"}])
            mock_self = mock.Mock()
            dh_views.GetNonexistentDomainHost.post.__wrapped__(mock_self, cb, clusterId="c1")
        _, kwargs = mock_self.response.call_args
        self.assertEqual(kwargs["data"], [{"host_id": "h2"}])


if __name__ == "__main__":
    unittest.main()
