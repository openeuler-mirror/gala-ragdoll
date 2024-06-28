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
"""
Time:
Author:
Description: Manager that start aops-zeus
"""
try:
    from gevent import monkey

    monkey.patch_all()
except:
    pass
from vulcanus import init_application
from vulcanus.database.proxy import RedisProxy
from vulcanus.registry.register_service.zookeeper import ZookeeperRegisterCenter
from vulcanus.timed import TimedTaskManager
from vulcanus.log.log import LOGGER
import socket
import _thread
from ragdoll.app.constant import TIMED_TASK_CONFIG_PATH
from ragdoll.app.core.subscription import TaskCallbackSubscribe
from ragdoll.app.cron import task_meta
from ragdoll.app.utils.prepare import Prepare
from ragdoll.app.settings import configuration
from ragdoll.urls import URLS


def load_prepare():
    git_dir = configuration.git.git_dir.replace("\"", "")
    git_user_name = configuration.git.user_name.replace("\"", "")
    git_user_email = configuration.git.user_email.replace("\"", "")

    prepare = Prepare(git_dir)
    prepare.mkdir_git_warehose(git_user_name, git_user_email)


def _init_timed_task(application):
    """
    Initialize and create a scheduled task

    Args:
        application:flask.Application
    """
    timed_task = TimedTaskManager(app=application, config_path=TIMED_TASK_CONFIG_PATH)
    if not timed_task.timed_config:
        LOGGER.warning(
            "If you want to start a scheduled task, please add a timed config."
        )
        return

    for task_info in timed_task.timed_config.values():
        task_type = task_info.get("type")
        if task_type not in task_meta:
            continue
        meta_class = task_meta[task_type]
        timed_task.add_job(meta_class(timed_config=task_info))

    timed_task.start()


def register_service():
    """
    register service
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(('8.8.8.8', 80))
        ip_address = sock.getsockname()[0]
    finally:
        sock.close()

    register_center = ZookeeperRegisterCenter(hosts=f"{configuration.zookeeper.host}:{configuration.zookeeper.port}")
    if not register_center.connected:
        register_center.connect()

    service_data = {"address": ip_address, "port": configuration.uwsgi.port}

    LOGGER.info("register ragdoll service")
    if not register_center.register_service(
            service_name="ragdoll_conf_trace_service", service_info=service_data, ephemeral=True
    ):
        raise RuntimeError("register ragdoll service failed")

    LOGGER.info("register ragdoll service success")


def main():
    _app = init_application(name="ragdoll", settings=configuration, register_urls=URLS)
    load_prepare()
    _init_timed_task(application=_app)
    register_service()
    _thread.start_new_thread(
        TaskCallbackSubscribe(subscribe_client=RedisProxy.redis_connect,
                              channels=["cluster_synchronize_cancel_task"])
    )
    return _app


app = main()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=configuration.uwsgi.port, debug=True)
