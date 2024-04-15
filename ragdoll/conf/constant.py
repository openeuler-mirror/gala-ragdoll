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
"""
Time:
Author:
Description: manager constant
"""
import os

from ragdoll.utils.git_tools import GitTools

BASE_CONFIG_PATH = "/etc/ragdoll/"

# path of manager configuration
MANAGER_CONFIG_PATH = os.path.join(BASE_CONFIG_PATH, 'gala-ragdoll.conf')

TARGETDIR = GitTools().target_dir

# domain
CREATE_DOMAIN = "/domain/createDomain"
DELETE_DOMAIN = "/domain/deleteDomain"
QUERY_DOMAIN = "/domain/queryDomain"

# host
ADD_HOST_IN_DOMAIN = "/host/addHost"
DELETE_HOST_IN_DOMAIN = "/host/deleteHost"
GET_HOST_BY_DOMAIN = "/host/getHost"

# management conf
ADD_MANAGEMENT_CONFS_IN_DOMAIN = "/management/addManagementConf"
UPLOAD_MANAGEMENT_CONFS_IN_DOMAIN = "/management/uploadManagementConf"
DELETE_MANAGEMENT_CONFS_IN_DOMAIN = "/management/deleteManagementConf"
GET_MANAGEMENT_CONFS_IN_DOMAIN = "/management/getManagementConf"
QUERY_CHANGELOG_OF_MANAGEMENT_CONFS_IN_DOMAIN = "/management/queryManageConfChange"

# confs
GET_SYNC_STATUS = "/confs/getDomainStatus"
QUERY_EXCEPTED_CONFS = "/confs/queryExpectedConfs"
QUERY_REAL_CONFS = "/confs/queryRealConfs"
SYNC_CONF_TO_HOST_FROM_DOMAIN = "/confs/syncConf"
QUERY_SUPPORTED_CONFS = "/confs/querySupportedConfs"
COMPARE_CONF_DIFF = "/confs/domain/diff"
BATCH_SYNC_CONF_TO_HOST_FROM_DOMAIN = "/confs/batch/syncConf"
