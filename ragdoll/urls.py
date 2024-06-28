#!/usr/bin/python3
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2021-2021. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN 'AS IS' BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************/
from ragdoll.app.views.confs import (
    GetTheSyncStatusOfDomain,
    QueryExceptedConfs,
    QueryRealConfs,
    SyncConfToHostFromDomain,
    QuerySupportedConfs,
    CompareConfDiff,
    BatchSyncConfToHostFromDomain
)
from ragdoll.app.views.domain import (
    CreateDomain,
    DeleteDomain,
    QueryDomain
)
from ragdoll.app.views.domain_confs import (
    AddManagementConfsInDomain,
    UploadManagementConfsInDomain,
    DeleteManagementConfsInDomain,
    GetManagementConfsInDomain,
    QueryChangelogOfManagementConfsInDomain
)
from ragdoll.app.views.domain_host import (
    AddHostInDomain,
    DeleteHostInDomain,
    GetHostByDomainName,
    GetNonexistentDomainHost
)
from ragdoll.app.views.host_conf_sync_status import GetHostConfSyncStatus
from vulcanus.conf import constant

URLS = [
    (CreateDomain, constant.CREATE_DOMAIN),
    (DeleteDomain, constant.DELETE_DOMAIN),
    (QueryDomain, constant.QUERY_DOMAIN),
    (AddHostInDomain, constant.ADD_HOST_IN_DOMAIN),
    (DeleteHostInDomain, constant.DELETE_HOST_IN_DOMAIN),
    (GetHostByDomainName, constant.GET_HOST_BY_DOMAIN),
    (GetNonexistentDomainHost, constant.GET_NOT_EXIST_HOST),
    (AddManagementConfsInDomain, constant.ADD_MANAGEMENT_CONFS_IN_DOMAIN),
    (UploadManagementConfsInDomain, constant.UPLOAD_MANAGEMENT_CONFS_IN_DOMAIN),
    (DeleteManagementConfsInDomain, constant.DELETE_MANAGEMENT_CONFS_IN_DOMAIN),
    (GetManagementConfsInDomain, constant.GET_MANAGEMENT_CONFS_IN_DOMAIN),
    (QueryChangelogOfManagementConfsInDomain, constant.QUERY_CHANGELOG_OF_MANAGEMENT_CONFS_IN_DOMAIN),
    (GetTheSyncStatusOfDomain, constant.GET_SYNC_STATUS),
    (QueryExceptedConfs, constant.QUERY_EXCEPTED_CONFS),
    (QueryRealConfs, constant.QUERY_REAL_CONFS),
    (SyncConfToHostFromDomain, constant.SYNC_CONF_TO_HOST_FROM_DOMAIN),
    (QuerySupportedConfs, constant.QUERY_SUPPORTED_CONFS),
    (CompareConfDiff, constant.COMPARE_CONF_DIFF),
    (BatchSyncConfToHostFromDomain, constant.BATCH_SYNC_CONF_TO_HOST_FROM_DOMAIN),
    (GetHostConfSyncStatus, constant.HOST_CONF_SYNC_STATUS)
]
