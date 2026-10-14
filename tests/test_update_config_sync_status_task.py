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
Description: unit tests for ragdoll/app/cron/update_config_sync_status_task.py
"""
import json
import unittest
from unittest import mock

from ragdoll.app.cron.update_config_sync_status_task import UpdateConfigSyncStatusTask
from vulcanus.restful.resp.state import SUCCEED

# Named constants (G.TYP.03: avoid hard-to-understand literals)
SYNC_STATUS_SYNCED = 1
SYNC_STATUS_NOT_SYNCED = 0
NON_SUCCEED_STATUS = 500


class TestGetDomainFiles(unittest.TestCase):
    """Tests for the static get_domain_files builder."""

    def test_collects_file_paths_per_domain(self):
        domain_paths = {}
        expected = [{"domainName": "dom", "confBaseInfos": [{"filePath": "/a"}, {"filePath": "/b"}]}]
        UpdateConfigSyncStatusTask.get_domain_files(domain_paths, expected)
        self.assertEqual(domain_paths, {"dom": ["/a", "/b"]})

    def test_empty_conf_base_infos(self):
        domain_paths = {}
        expected = [{"domainName": "dom", "confBaseInfos": []}]
        UpdateConfigSyncStatusTask.get_domain_files(domain_paths, expected)
        self.assertEqual(domain_paths, {"dom": []})

    def test_missing_conf_base_infos(self):
        domain_paths = {}
        expected = [{"domainName": "dom"}]
        UpdateConfigSyncStatusTask.get_domain_files(domain_paths, expected)
        self.assertEqual(domain_paths, {"dom": []})


class TestDealHostFileContent(unittest.TestCase):
    """Tests for the static deal_host_file_content transformation."""

    def test_non_directory_files_collected(self):
        domain_result = {}
        hfc = {"host_id": "h1", "infos": [{"path": "/etc/hostname", "content": "aops"}]}
        UpdateConfigSyncStatusTask.deal_host_file_content(domain_result, hfc)
        self.assertEqual(domain_result, {"h1": [{"filePath": "/etc/hostname", "contents": "aops"}]})

    def test_pam_d_files_aggregated(self):
        domain_result = {}
        hfc = {"host_id": "h1", "infos": [
            {"path": "/etc/pam.d/sshd", "content": "x"},
            {"path": "/etc/pam.d/login", "content": "y"},
        ]}
        UpdateConfigSyncStatusTask.deal_host_file_content(domain_result, hfc)
        entry = domain_result.get("h1")[0]
        self.assertEqual(entry.get("filePath"), "/etc/pam.d")
        self.assertEqual(
            json.loads(entry.get("contents")),
            {"/etc/pam.d/sshd": "x", "/etc/pam.d/login": "y"})

    def test_empty_infos_leaves_result_empty(self):
        domain_result = {}
        hfc = {"host_id": "h1", "infos": []}
        UpdateConfigSyncStatusTask.deal_host_file_content(domain_result, hfc)
        self.assertEqual(domain_result, {})


class TestGetDomainHostIds(unittest.TestCase):
    """Tests for the static get_domain_host_ids against a mock proxy."""

    def test_collects_host_ids(self):
        proxy = mock.Mock()
        proxy.get_domain_host_sync_status.return_value = (
            SUCCEED, [{"host_id": "h1"}, {"host_id": "h2"}])
        result = UpdateConfigSyncStatusTask.get_domain_host_ids([{"domainName": "dom"}], proxy)
        self.assertEqual(result, {"dom": ["h1", "h2"]})

    def test_skips_when_not_succeed(self):
        proxy = mock.Mock()
        proxy.get_domain_host_sync_status.return_value = (NON_SUCCEED_STATUS, [])
        result = UpdateConfigSyncStatusTask.get_domain_host_ids([{"domainName": "dom"}], proxy)
        self.assertEqual(result, {})


class TestCompareConf(unittest.TestCase):
    """Tests for the static compare_conf sync-status resolution."""

    def test_all_synced(self):
        self.assertEqual(
            self._compare("SYNCED"),
            [{"domain_name": "dom", "host_id": "h1", "sync_status": SYNC_STATUS_SYNCED}])

    def test_not_synced(self):
        self.assertEqual(
            self._compare("NOT SYNCHRONIZE"),
            [{"domain_name": "dom", "host_id": "h1", "sync_status": SYNC_STATUS_NOT_SYNCED}])

    def _compare(self, is_synced):
        with mock.patch("ragdoll.app.utils.format.Format") as m_format:
            m_format.deal_expected_confs_resp.return_value = {"dom": {}}
            m_format.deal_domain_result.return_value = {"dom": [{}]}
            m_format.diff_mangeconf_with_realconf_for_db.return_value = {
                "domainName": "dom",
                "hostStatus": [{"hostId": "h1", "syncStatus": [{"isSynced": is_synced}]}],
            }
            return UpdateConfigSyncStatusTask.compare_conf([{}], {})


if __name__ == "__main__":
    unittest.main()
