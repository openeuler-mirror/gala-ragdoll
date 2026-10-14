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
Description: unit tests for ragdoll/app/core/subscription.py
"""
import unittest
from unittest import mock

from ragdoll.app.core.subscription import TaskCallbackSubscribe
from vulcanus.exceptions.database_exception import DatabaseConnectionFailed


def make_subscriber(client=None):
    """Build a TaskCallbackSubscribe with a mock redis client."""
    if client is None:
        client = mock.Mock()
    return TaskCallbackSubscribe(
        subscribe_client=client,
        channels=["cluster_synchronize_cancel_task", "host_delete_task"],
    )


class TestInit(unittest.TestCase):
    """Tests for TaskCallbackSubscribe.__init__."""

    def test_stores_arguments(self):
        client = mock.Mock()
        sub = TaskCallbackSubscribe(subscribe_client=client, channels=["a", "b"])
        self.assertEqual(sub._subscribe, client)
        self.assertEqual(sub._channels, ["a", "b"])
        self.assertIsNone(sub.subscribe_message)


class TestCallbackDispatch(unittest.TestCase):
    """Tests for the _callback channel dispatch."""

    def test_dispatches_to_matching_method(self):
        sub = make_subscriber()
        with mock.patch.object(sub, "_cluster_synchronize_cancel_task") as handler:
            sub._callback("cluster_synchronize_cancel_task", {"cluster_id": "c1"})
        handler.assert_called_once_with({"cluster_id": "c1"})

    def test_non_callable_handler_is_ignored(self):
        """A handler attribute that exists but is not callable is logged and skipped."""
        sub = make_subscriber()
        sub._unavailable = None
        with mock.patch("ragdoll.app.core.subscription.LOGGER") as logger:
            sub._callback("unavailable", {"x": 1})
        logger.error.assert_called_once_with("Unsupported task type")


class TestClusterSynchronizeCancelTask(unittest.TestCase):
    """Tests for _cluster_synchronize_cancel_task branches."""

    def test_skips_when_lock_already_held(self):
        client = mock.Mock()
        client.set.return_value = False
        sub = make_subscriber(client)
        with mock.patch("ragdoll.app.core.subscription.ConfTraceProxy") as proxy_cls:
            sub._cluster_synchronize_cancel_task({"cluster_id": "c1"})
        proxy_cls.assert_not_called()

    def test_cancels_cluster_when_lock_acquired(self):
        client = mock.Mock()
        client.set.return_value = True
        sub = make_subscriber(client)
        proxy = mock.Mock()
        with mock.patch("ragdoll.app.core.subscription.ConfTraceProxy") as proxy_cls:
            proxy_cls.return_value.__enter__.return_value = proxy
            sub._cluster_synchronize_cancel_task({"cluster_id": "c1"})
        client.set.assert_called_once_with(
            "cluster_synchronize_cancel_task_ragdoll_subscribe-c1",
            "locked", nx=True, ex=30,
        )
        proxy.cancel_synchronize_cluster.assert_called_once_with("c1")

    def test_database_error_is_swallowed(self):
        client = mock.Mock()
        client.set.return_value = True
        sub = make_subscriber(client)
        proxy = mock.Mock()
        proxy.cancel_synchronize_cluster.side_effect = DatabaseConnectionFailed("db down")
        with mock.patch("ragdoll.app.core.subscription.ConfTraceProxy") as proxy_cls:
            proxy_cls.return_value.__enter__.return_value = proxy
            sub._cluster_synchronize_cancel_task({"cluster_id": "c1"})
        proxy.cancel_synchronize_cluster.assert_called_once_with("c1")


class TestHostDeleteTask(unittest.TestCase):
    """Tests for _host_delete_task branches."""

    def test_skips_when_lock_already_held(self):
        client = mock.Mock()
        client.set.return_value = False
        sub = make_subscriber(client)
        with mock.patch("ragdoll.app.core.subscription.ConfTraceProxy") as proxy_cls:
            sub._host_delete_task([1, 2])
        proxy_cls.assert_not_called()

    def test_cancels_hosts_when_lock_acquired(self):
        client = mock.Mock()
        client.set.return_value = True
        sub = make_subscriber(client)
        proxy = mock.Mock()
        with mock.patch("ragdoll.app.core.subscription.ConfTraceProxy") as proxy_cls:
            proxy_cls.return_value.__enter__.return_value = proxy
            sub._host_delete_task([1, 2])
        client.set.assert_called_once_with(
            "host_delete_task_ragdoll_subscribe-[1, 2]", "locked", nx=True, ex=30
        )
        proxy.host_cancel.assert_called_once_with([1, 2])

    def test_database_error_is_swallowed(self):
        client = mock.Mock()
        client.set.return_value = True
        sub = make_subscriber(client)
        proxy = mock.Mock()
        proxy.host_cancel.side_effect = DatabaseConnectionFailed("db down")
        with mock.patch("ragdoll.app.core.subscription.ConfTraceProxy") as proxy_cls:
            proxy_cls.return_value.__enter__.return_value = proxy
            sub._host_delete_task([1, 2])
        proxy.host_cancel.assert_called_once_with([1, 2])


if __name__ == "__main__":
    unittest.main()
