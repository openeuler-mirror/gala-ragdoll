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
# pylint: disable=protected-access
"""
Description: unit tests for ragdoll/app/proxy/domain.py
"""
import unittest
from unittest import mock

from ragdoll.app.proxy.domain import DomainProxy


def make_proxy():
    """Build a DomainProxy without DB setup, with a mocked session."""
    proxy = DomainProxy.__new__(DomainProxy)
    proxy.session = mock.Mock()
    return proxy


class TestGetDomainsPageFilters(unittest.TestCase):
    """Tests for the static _get_domains_page_filters builder."""

    def test_empty_cluster_list(self):
        self.assertEqual(DomainProxy._get_domains_page_filters({"cluster_list": []}), set())

    def test_cluster_list_adds_in_filter(self):
        filters = DomainProxy._get_domains_page_filters({"cluster_list": ["c1", "c2"]})
        self.assertEqual(len(filters), 1)
        clause = next(iter(filters))
        self.assertIn("cluster_id", str(clause))


class TestQueryDomainsPage(unittest.TestCase):
    """Tests for _query_domains_page against a mocked session."""

    def test_zero_count_returns_empty_result(self):
        proxy = make_proxy()
        proxy.session.query.return_value.filter.return_value.count.return_value = 0
        result = proxy._query_domains_page({"cluster_list": []})
        self.assertEqual(result, {"total_count": 0, "total_page": 0, "domain_infos": []})


class TestQueryDomainByName(unittest.TestCase):
    """Tests for query_domain_by_name against a mocked session."""

    def test_returns_first_match(self):
        proxy = make_proxy()
        fake_domain = mock.Mock()
        proxy.session.query.return_value.filter.return_value.first.return_value = fake_domain
        result = proxy.query_domain_by_name("aops")
        self.assertIs(result, fake_domain)


class TestGetAllDomains(unittest.TestCase):
    """Tests for get_all_domains against a mocked session."""

    def test_returns_all_domains(self):
        proxy = make_proxy()
        fake_domains = [mock.Mock(), mock.Mock()]
        proxy.session.query.return_value.all.return_value = fake_domains
        self.assertEqual(proxy.get_all_domains(), fake_domains)


if __name__ == "__main__":
    unittest.main()
