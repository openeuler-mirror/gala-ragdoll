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
from vulcanus.registry.register_service.zookeeper import ZookeeperRegisterCenter
from vulcanus.log.log import LOGGER
import socket
from ragdoll.app.settings import configuration
from ragdoll.urls import URLS


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
    register_service()
    return _app


app = main()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=configuration.uwsgi.port, debug=True)
