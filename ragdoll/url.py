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
@FileName: url.py
@Time: 2024/3/4 10:31
@Author: JiaoSiMao
Description:
"""
from ragdoll.conf.constant import (
    CREATE_DOMAIN, DELETE_DOMAIN, QUERY_DOMAIN, ADD_HOST_IN_DOMAIN, DELETE_HOST_IN_DOMAIN, GET_HOST_BY_DOMAIN,
    ADD_MANAGEMENT_CONFS_IN_DOMAIN, UPLOAD_MANAGEMENT_CONFS_IN_DOMAIN, DELETE_MANAGEMENT_CONFS_IN_DOMAIN,
    GET_MANAGEMENT_CONFS_IN_DOMAIN, QUERY_CHANGELOG_OF_MANAGEMENT_CONFS_IN_DOMAIN, GET_SYNC_STATUS,
    QUERY_EXCEPTED_CONFS, QUERY_REAL_CONFS, SYNC_CONF_TO_HOST_FROM_DOMAIN, QUERY_SUPPORTED_CONFS, COMPARE_CONF_DIFF,
    BATCH_SYNC_CONF_TO_HOST_FROM_DOMAIN
)
from ragdoll.domain_manage import view as domain_view
from ragdoll.host_manage import view as host_view
from ragdoll.domain_conf_manage import view as domain_conf_view
from ragdoll.confs_manage import view as confs_view
URLS = []

SPECIFIC_URLS = {
    "DOMAIN_URLS": [
        (domain_view.CreateDomain, CREATE_DOMAIN),
        (domain_view.DeleteDomain, DELETE_DOMAIN),
        (domain_view.QueryDomain, QUERY_DOMAIN),
    ],
    "HOST_URLS": [
        (host_view.AddHostInDomain, ADD_HOST_IN_DOMAIN),
        (host_view.DeleteHostInDomain, DELETE_HOST_IN_DOMAIN),
        (host_view.GetHostByDomainName, GET_HOST_BY_DOMAIN),
    ],
    "MANAGEMENT_URLS": [
        (domain_conf_view.AddManagementConfsInDomain, ADD_MANAGEMENT_CONFS_IN_DOMAIN),
        (domain_conf_view.UploadManagementConfsInDomain, UPLOAD_MANAGEMENT_CONFS_IN_DOMAIN),
        (domain_conf_view.DeleteManagementConfsInDomain, DELETE_MANAGEMENT_CONFS_IN_DOMAIN),
        (domain_conf_view.GetManagementConfsInDomain, GET_MANAGEMENT_CONFS_IN_DOMAIN),
        (domain_conf_view.QueryChangelogOfManagementConfsInDomain, QUERY_CHANGELOG_OF_MANAGEMENT_CONFS_IN_DOMAIN),
    ],
    "CONFS_URLS": [
        (confs_view.GetTheSyncStatusOfDomain, GET_SYNC_STATUS),
        (confs_view.QueryExceptedConfs, QUERY_EXCEPTED_CONFS),
        (confs_view.QueryRealConfs, QUERY_REAL_CONFS),
        (confs_view.SyncConfToHostFromDomain, SYNC_CONF_TO_HOST_FROM_DOMAIN),
        (confs_view.QuerySupportedConfs, QUERY_SUPPORTED_CONFS),
        (confs_view.CompareConfDiff, COMPARE_CONF_DIFF),
        (confs_view.BatchSyncConfToHostFromDomain, BATCH_SYNC_CONF_TO_HOST_FROM_DOMAIN),
    ]
}

for _, value in SPECIFIC_URLS.items():
    URLS.extend(value)
