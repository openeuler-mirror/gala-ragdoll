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
Description: unit tests for ragdoll/app/proxy/domain_conf_info.py
"""
import unittest
from unittest import mock

import sqlalchemy

from ragdoll.app.proxy.domain_conf_info import DomainConfInfoProxy
from vulcanus.restful.resp.state import (
    SUCCEED, DATABASE_INSERT_ERROR,
)


def make_proxy():
    """Build a DomainConfInfoProxy without DB setup, with a mocked session."""
    proxy = DomainConfInfoProxy.__new__(DomainConfInfoProxy)
    proxy.session = mock.Mock()
    return proxy


def _set_domain(proxy, domain_id=42):
    """Wire a mock session so the Domain lookup returns a fake domain row."""
    fake_domain = mock.Mock()
    fake_domain.domain_id = domain_id
    q = proxy.session.query.return_value
    q.filter.return_value.first.return_value = fake_domain
    return q


class TestAddDomainConf(unittest.TestCase):
    """Tests for add_domain_conf success / update / error branches."""

    def test_new_conf_is_added(self):
        proxy = make_proxy()
        q = _set_domain(proxy)
        q.filter.return_value.filter.return_value.first.return_value = None  # no existing row
        result = proxy.add_domain_conf("aops", {"/etc/hostname": "aops"})
        self.assertEqual(result, SUCCEED)
        proxy.session.add.assert_called_once()
        proxy.session.commit.assert_called_once()

    def test_existing_conf_is_updated(self):
        proxy = make_proxy()
        q = _set_domain(proxy)
        existing = mock.Mock()
        q.filter.return_value.filter.return_value.first.return_value = existing
        result = proxy.add_domain_conf("aops", {"/etc/hostname": "new-value"})
        self.assertEqual(result, SUCCEED)
        proxy.session.add.assert_not_called()
        self.assertEqual(existing.conf_info, "new-value")
        proxy.session.commit.assert_called_once()

    def test_db_error_returns_insert_error(self):
        proxy = make_proxy()
        proxy.session.query.side_effect = sqlalchemy.exc.SQLAlchemyError("boom")
        result = proxy.add_domain_conf("aops", {"/etc/hostname": "aops"})
        self.assertEqual(result, DATABASE_INSERT_ERROR)
        proxy.session.rollback.assert_called_once()


class TestDeleteDomainConfs(unittest.TestCase):
    """Tests for delete_domain_confs success branch."""

    def test_deletes_matching_confs(self):
        proxy = make_proxy()
        q = _set_domain(proxy)
        result = proxy.delete_domain_confs("aops", [{"filePath": "/etc/hostname"}])
        self.assertEqual(result, SUCCEED)
        q.filter.return_value.filter.return_value.delete.assert_called_once()
        proxy.session.commit.assert_called_once()


class TestGetDomainConfsByDomain(unittest.TestCase):
    """Tests for get_domain_confs_by_domain success branch."""

    def test_returns_conf_files(self):
        proxy = make_proxy()
        q = _set_domain(proxy)
        conf1 = mock.Mock()
        conf1.conf_path = "/etc/hostname"
        conf1.conf_info = "aops"
        conf2 = mock.Mock()
        conf2.conf_path = "/etc/hosts"
        conf2.conf_info = "127.0.0.1"
        q.filter.return_value.all.return_value = [conf1, conf2]
        status, payload = proxy.get_domain_confs_by_domain("aops")
        self.assertEqual(status, SUCCEED)
        self.assertEqual(payload.get("domainName"), "aops")
        self.assertEqual(len(payload.get("confFiles")), 2)
        self.assertEqual(payload.get("confFiles")[0], {"filePath": "/etc/hostname", "contents": "aops"})


if __name__ == "__main__":
    unittest.main()
