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
Description: unit tests for ragdoll/app/proxy/domain_host.py
"""
import unittest
from unittest import mock

import sqlalchemy

from ragdoll.app.proxy.domain_host import DomainHostProxy
from vulcanus.restful.resp.state import SUCCEED, DATABASE_INSERT_ERROR


def make_proxy():
    """Build a DomainHostProxy without DB setup, with a mocked session."""
    proxy = DomainHostProxy.__new__(DomainHostProxy)
    proxy.session = mock.Mock()
    return proxy


def _set_domain(proxy, domain_id=7):
    fake_domain = mock.Mock()
    fake_domain.domain_id = domain_id
    q = proxy.session.query.return_value
    q.filter.return_value.first.return_value = fake_domain
    return q


class TestAddDomainHosts(unittest.TestCase):
    """Tests for add_domain_hosts success / error branches."""

    def test_adds_hosts_and_commits(self):
        proxy = make_proxy()
        _set_domain(proxy)
        host_infos = [{"hostId": "h1", "ip": "1.1.1.1", "ipv6": "::1"}]
        result = proxy.add_domain_hosts("aops", host_infos)
        self.assertEqual(result, SUCCEED)
        proxy.session.add_all.assert_called_once()
        proxy.session.commit.assert_called_once()

    def test_db_error_returns_insert_error(self):
        proxy = make_proxy()
        proxy.session.query.side_effect = sqlalchemy.exc.SQLAlchemyError("boom")
        result = proxy.add_domain_hosts("aops", [{"hostId": "h1", "ip": "1.1.1.1", "ipv6": "::1"}])
        self.assertEqual(result, DATABASE_INSERT_ERROR)
        proxy.session.rollback.assert_called_once()


class TestDeleteDomainHost(unittest.TestCase):
    """Tests for delete_domain_host success branch."""

    def test_deletes_matching_hosts(self):
        proxy = make_proxy()
        q = _set_domain(proxy)
        result = proxy.delete_domain_host("aops", [{"hostId": "h1"}])
        self.assertEqual(result, SUCCEED)
        q.filter.return_value.filter.return_value.delete.assert_called_once()
        proxy.session.commit.assert_called_once()


class TestGetDomainHostByDomain(unittest.TestCase):
    """Zero-row early return of get_domain_host_by_domain."""

    def test_zero_count_returns_empty_result(self):
        proxy = make_proxy()
        q = _set_domain(proxy)
        query = q.outerjoin.return_value.outerjoin.return_value.filter.return_value
        query.count.return_value = 0
        params = {"domainName": "aops", "hostIp": None, "sync_status": None,
                  "per_page": 10, "page": 1}
        status, result = proxy.get_domain_host_by_domain(params)
        self.assertEqual(status, SUCCEED)
        self.assertEqual(result["total_count"], 0)
        self.assertEqual(result["hostlist"], [])


class TestGetDomainHostByDomainIdList(unittest.TestCase):
    """Tests for get_domain_host_by_domain_id_list success branch."""

    def test_builds_host_list(self):
        proxy = make_proxy()
        q = proxy.session.query.return_value
        host1 = mock.Mock()
        host1.host_id, host1.host_ip, host1.ipv6 = "h1", "1.1.1.1", None
        host2 = mock.Mock()
        host2.host_id, host2.host_ip, host2.ipv6 = "h2", "2.2.2.2", None
        q.filter.return_value.all.return_value = [host1, host2]
        status, hostlist = proxy.get_domain_host_by_domain_id_list(["d1"])
        self.assertEqual(status, SUCCEED)
        self.assertEqual(hostlist, [
            {"hostId": "h1", "ip": "1.1.1.1", "ipv6": None},
            {"hostId": "h2", "ip": "2.2.2.2", "ipv6": None},
        ])


class TestGetDomainHostByHostId(unittest.TestCase):
    """Tests for get_domain_host_by_host_id success branch."""

    def test_returns_first_match(self):
        proxy = make_proxy()
        fake = mock.Mock()
        proxy.session.query.return_value.filter.return_value.first.return_value = fake
        status, info = proxy.get_domain_host_by_host_id("h1")
        self.assertEqual(status, SUCCEED)
        self.assertIs(info, fake)


if __name__ == "__main__":
    unittest.main()
