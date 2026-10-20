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
Description: unit tests for ragdoll/app/proxy/conf_trace.py
"""
import unittest
from unittest import mock

from ragdoll.app.proxy.conf_trace import ConfTraceProxy


def make_proxy(count=0):
    """Build a ConfTraceProxy without DB setup, with a mocked session."""
    proxy = ConfTraceProxy.__new__(ConfTraceProxy)
    session = mock.Mock()
    session.query.return_value.filter.return_value.scalar.return_value = count
    proxy.session = session
    return proxy


class TestGetConfTraceFilters(unittest.TestCase):
    """Tests for the static _get_conf_trace_filters builder."""

    def test_no_filters_for_empty_data(self):
        self.assertEqual(ConfTraceProxy._get_conf_trace_filters({}), set())

    def test_one_filter_per_present_key(self):
        filters = ConfTraceProxy._get_conf_trace_filters(
            {"domain_name": "d", "host_id": 5, "conf_name": "c"})
        self.assertEqual(len(filters), 3)

    def test_partial_keys(self):
        filters = ConfTraceProxy._get_conf_trace_filters({"host_id": 5, "conf_name": "c"})
        self.assertEqual(len(filters), 2)

    def test_domain_name_filter_column(self):
        filters = ConfTraceProxy._get_conf_trace_filters({"domain_name": "d"})
        clause = next(iter(filters))
        self.assertIn("domain_name", str(clause))

    def test_host_id_filter_column(self):
        filters = ConfTraceProxy._get_conf_trace_filters({"host_id": 5})
        clause = next(iter(filters))
        self.assertIn("host_id", str(clause))

    def test_conf_name_filter_column(self):
        filters = ConfTraceProxy._get_conf_trace_filters({"conf_name": "c"})
        clause = next(iter(filters))
        self.assertIn("conf_name", str(clause))


class TestGetConfChangeRecordFilters(unittest.TestCase):
    """Tests for the static _get_conf_change_record_filters builder."""

    def test_no_filters_for_empty_data(self):
        self.assertEqual(ConfTraceProxy._get_conf_change_record_filters({}), set())

    def test_all_keys(self):
        filters = ConfTraceProxy._get_conf_change_record_filters(
            {"domain_name": "d", "host_ip": "1.1.1.1", "conf_name": "c"})
        self.assertEqual(len(filters), 3)

    def test_host_ip_filter_column(self):
        filters = ConfTraceProxy._get_conf_change_record_filters({"host_ip": "1.1.1.1"})
        clause = next(iter(filters))
        self.assertIn("host_ip", str(clause))


class TestGetConfTraceCount(unittest.TestCase):
    """Tests for _get_conf_trace_count against a mocked session."""

    def test_returns_session_scalar(self):
        proxy = make_proxy(count=7)
        self.assertEqual(proxy._get_conf_trace_count(set()), 7)


class TestSortMethodsZeroCount(unittest.TestCase):
    """Zero-row early returns for the two sort/query builders."""

    def test_sort_trace_info_zero_count(self):
        proxy = make_proxy(count=0)
        result = proxy._sort_trace_info_by_column({"sort": "create_time"})
        self.assertEqual(
            result, {"total_count": 0, "total_page": 0, "conf_trace_infos": []})

    def test_sort_conf_change_record_zero_count(self):
        proxy = make_proxy(count=0)
        result = proxy._sort_conf_change_record_by_column({"sort": "create_time"})
        self.assertEqual(
            result, {"total_count": 0, "total_page": 0, "conf_change_records": []})


if __name__ == "__main__":
    unittest.main()
