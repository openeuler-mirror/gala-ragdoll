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
@FileName: __init__.py.py
@Time: 2024/5/24 11:00
@Author: JiaoSiMao
Description:
"""
from ragdoll.app.settings import configuration
from ragdoll.app.utils.git_tools import GitTools

from vulcanus.cache import RedisCacheManage
from vulcanus.database.proxy import RedisProxy

if RedisProxy.redis_connect is None:
    RedisProxy()

cache = RedisCacheManage(domain=configuration.domain, redis_client=RedisProxy.redis_connect)
TARGETDIR = GitTools().target_dir