#!/usr/bin/python3
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
import json
import time
from typing import List

from redis import Redis, RedisError
from vulcanus.conf.constant import TaskStatus
from vulcanus.exceptions.database_exception import DatabaseConnectionFailed
from vulcanus.log.log import LOGGER
from ragdoll.app.proxy.conf_trace import ConfTraceProxy

__all__ = ['TaskCallbackSubscribe']


class TaskCallbackSubscribe:
    """
    Handles callback logic for different task channels.
    """

    def __init__(self, subscribe_client: Redis, channels: List[str]) -> None:
        self._subscribe = subscribe_client
        self._channels = channels
        self.subscribe_message = None

    def __call__(self, *args, **kwds):
        """
        Subscribe to Redis channels and execute a callback function for each received message.
        """
        while True:
            try:
                subscribe = self._subscribe.pubsub()
                for channel in self._channels:
                    subscribe.subscribe(channel)

                for message in subscribe.listen():
                    if message["type"] != "message":
                        continue

                    self._callback(message["channel"], json.loads(message["data"]))
            except RedisError as error:
                LOGGER.error(f"Failed to subscribe to channels {self._channels}: {error}")
                time.sleep(1)

    def _cluster_synchronize_cancel_task(self, task_execute_result: dict) -> None:
        lock = f"cluster_synchronize_cancel_task_ragdoll_subscribe-{task_execute_result['cluster_id']}"
        if not self._subscribe.set(lock, 'locked', nx=True, ex=30):
            LOGGER.warning("Another repo set task is running, skip this subscribe.")
            return
        try:
            with ConfTraceProxy() as proxy:
                proxy.cancel_synchronize_cluster(task_execute_result.get("cluster_id"))
        except DatabaseConnectionFailed:
            LOGGER.error(f"Failed to delete cluster: {task_execute_result.get('cluster_id')} relative info.")

    def _callback(self, channel: str, task_execute_result: dict) -> None:
        """
        Handles callback based on the task channel and task execution result.

        Args:
            channel (str): The name of the task channel.
            task_execute_result (dict): The result of the task execution.
        """
        channel_func = getattr(self, f"_{channel}")
        if not channel_func or not callable(channel_func):
            LOGGER.error("Unsupported task type")
            return

        if task_execute_result.get("status") == TaskStatus.SUCCEED:
            channel_func(task_execute_result)
