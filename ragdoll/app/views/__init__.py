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
@Time: 2024/5/24 11:08
@Author: JiaoSiMao
Description:
"""
from .domain import (
    CreateDomain,
    DeleteDomain,
    QueryDomain
)
from .domain_confs import (
    AddManagementConfsInDomain,
    UploadManagementConfsInDomain,
    DeleteManagementConfsInDomain,
    GetManagementConfsInDomain,
    QueryChangelogOfManagementConfsInDomain
)
from .domain_host import (
    AddHostInDomain,
    DeleteHostInDomain,
    GetHostByDomainName
)
from .host_conf_sync_status import GetHostConfSyncStatus

__all__ = (
    "CreateDomain",
    "DeleteDomain",
    "QueryDomain",
    "AddHostInDomain",
    "DeleteHostInDomain",
    "GetHostByDomainName",
    "AddManagementConfsInDomain",
    "UploadManagementConfsInDomain",
    "DeleteManagementConfsInDomain",
    "GetManagementConfsInDomain",
    "QueryChangelogOfManagementConfsInDomain",
    "GetHostConfSyncStatus"
)
