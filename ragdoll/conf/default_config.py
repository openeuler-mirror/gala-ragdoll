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
Description: default config of manager
"""
git = {"GIT_DIR": "/home/confTraceTest", "USER_NAME": "user_name", "USER_EMAIL": "user_email"}

collect = {
    "COLLECT_ADDRESS": "http://127.0.0.1",
    "COLLECT_API": "/manage/config/collect",
    "COLLECT_PORT": 11111
}

sync = {
    "SYNC_ADDRESS": "http://127.0.0.1",
    "SYNC_API": "/manage/config/sync",
    "BATCH_SYNC_ADDRESS": "http://127.0.0.1",
    "BATCH_SYNC_API": "/manage/config/batch/sync",
    "SYNC_PORT": 11111
}

objectFile = {"OBJECT_FILE_ADDRESS": "http://127.0.0.1", "OBJECT_FILE_API": "/manage/config/objectfile",
              "OBJECT_FILE_PORT": 11111}

sync_status = {
    "HOST_SYNC_STATUS_ADDRESS": "http://127.0.0.1",
    "ADD_HOST_SYNC_STATUS_API": "/manage/host/sync/status/add",
    "DELETE_HOST_SYNC_STATUS_API": "/manage/host/sync/status/delete",
    "HOST_SYNC_STATUS_PORT": 11111
}

ragdoll = {"IP": "127.0.0.1", "PORT": 11114}

mysql = {
    "IP": "127.0.0.1",
    "PORT": 3306,
    "DATABASE_NAME": "aops",
    "ENGINE_FORMAT": "mysql+pymysql://@%s:%s/%s",
    "POOL_SIZE": 100,
    "POOL_RECYCLE": 7200,
}

redis = {"IP": "127.0.0.1", "PORT": 6379}

log = {"LOG_LEVEL": "INFO", "LOG_DIR": "/var/log/aops", "MAX_BYTES": 31457280, "BACKUP_COUNT": 40}


