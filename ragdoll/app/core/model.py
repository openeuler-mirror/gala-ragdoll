#!/usr/bin/python3
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2022-2022. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN 'AS IS' BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************/
from dataclasses import dataclass


@dataclass
class ClientConnectArgs:
    """ClientConnectArgs - model defined

    Args:
        host_ip: host public ip
        ssh_port: ssh remote login port
        ssh_user: ssh remote login user
        pkey: RSA-KEY string used for authentication
        timeout: timeout opening a channel, default 10s

    """

    host_ip: str
    ssh_port: int
    ssh_user: str
    pkey: str
    timeout: float = 10
