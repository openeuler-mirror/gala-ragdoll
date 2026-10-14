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
Description: unit tests for ragdoll/app/proxy/host_conf_sync_status.py
"""
import unittest
from unittest import mock

import sqlalchemy

from ragdoll.app.proxy.host_conf_sync_status import HostConfSyncStatusProxy
from vulcanus.restful.resp.state import (
    SUCCEED, DATABASE_INSERT_ERROR, DATABASE_QUERY_ERROR,
)


def make_proxy():
    """Build a HostConfSyncStatusProxy without DB setup, with a mocked session."""
    proxy = HostConfSyncStatusProxy.__new__(HostConfSyncStatusProxy)
    proxy.session = mock.Mock()
    return proxy


class TestAddHostSyncStatus(unittest.TestCase):
    """Tests for add_host_sync_status success / error branches."""

    def test_adds_statuses_and_commits(self):
        proxy = make_proxy()
        fake_domain = mock.Mock()
        proxy.session.query.return_value.filter.return_value.first.return_value = fake_domain
        result = proxy.add_host_sync_status("aops", [{"host_id": "h1", "host_ip": "1.1.1.1"}])
        self.assertEqual(result, SUCCEED)
        proxy.session.add_all.assert_called_once()
        proxy.session.commit.assert_called_once()

    def test_db_error_returns_insert_error(self):
        proxy = make_proxy()
        proxy.session.query.side_effect = sqlalchemy.exc.SQLAlchemyError("boom")
        result = proxy.add_host_sync_status("aops", [{"host_id": "h1", "host_ip": "1.1.1.1"}])
        self.assertEqual(result, DATABASE_INSERT_ERROR)
        proxy.session.rollback.assert_called_once()


class TestDeleteHostSyncStatus(unittest.TestCase):
    """Tests for delete_host_sync_status success branch."""

    def test_deletes_matching_statuses(self):
        proxy = make_proxy()
        q = proxy.session.query.return_value
        result = proxy.delete_host_sync_status("d1", ["h1"])
        self.assertEqual(result, SUCCEED)
        q.filter.return_value.filter.return_value.delete.assert_called_once()
        proxy.session.commit.assert_called_once()


class TestGetDomainHostSyncStatus(unittest.TestCase):
    """Tests for get_domain_host_sync_status success branch."""

    def test_builds_status_list(self):
        proxy = make_proxy()
        q = proxy.session.query.return_value
        qf = q.filter.return_value
        qf.first.return_value = mock.Mock()  # domain lookup
        host1 = mock.Mock()
        host1.host_id, host1.host_ip, host1.sync_status = "h1", "1.1.1.1", 1
        host2 = mock.Mock()
        host2.host_id, host2.host_ip, host2.sync_status = "h2", "2.2.2.2", 0
        qf.all.return_value = [host1, host2]
        status, result = proxy.get_domain_host_sync_status("aops")
        self.assertEqual(status, SUCCEED)
        self.assertEqual(result, [
            {"host_id": "h1", "host_ip": "1.1.1.1", "sync_status": 1},
            {"host_id": "h2", "host_ip": "2.2.2.2", "sync_status": 0},
        ])
        proxy.session.commit.assert_called_once()


class TestUpdateDomainHostSyncStatus(unittest.TestCase):
    """Tests for update_domain_host_sync_status populated / empty branches."""

    def test_updates_and_returns_counts(self):
        proxy = make_proxy()
        q = proxy.session.query.return_value
        qf = q.filter.return_value
        qf.first.return_value = mock.Mock()  # domain lookup
        qf.filter.return_value.update.return_value = 1
        diff = [{"domain_name": "aops", "host_id": "h1", "sync_status": 1}]
        status, saved_ids = proxy.update_domain_host_sync_status(diff)
        self.assertEqual(status, SUCCEED)
        self.assertEqual(saved_ids, [1])
        proxy.session.commit.assert_called_once()

    def test_empty_input_returns_query_error(self):
        proxy = make_proxy()
        status, saved_ids = proxy.update_domain_host_sync_status([])
        self.assertEqual(status, DATABASE_QUERY_ERROR)
        self.assertEqual(saved_ids, [])


if __name__ == "__main__":
    unittest.main()
