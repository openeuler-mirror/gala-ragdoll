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
@FileName: host_conf_sync_status.py
@Time: 2024/6/14 15:52
@Author: JiaoSiMao
Description:
"""
from marshmallow import Schema, fields


class GetHostConfSyncStatusSchema(Schema):
    """
    validators for parameter of /conftrace/host/sync/status/get
    """
    domainName = fields.String(required=True, validate=lambda s: len(s) > 0)
