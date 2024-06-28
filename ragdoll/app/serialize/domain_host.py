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
@FileName: domain_host.py
@Time: 2024/3/5 9:44
@Author: JiaoSiMao
Description:
"""
from marshmallow import Schema, fields


class HostSchema(Schema):
    """
    validators for parameter of host
    """
    hostId = fields.String(required=True, validate=lambda s: len(s) > 0)
    ip = fields.String(required=True, validate=lambda s: len(s) > 0)
    ipv6 = fields.String(required=True, validate=lambda s: len(s) > 0)


class SingleDeleteHostSchema(Schema):
    """
    validators for parameter of /host/deleteHost
    """
    hostId = fields.String(required=True, validate=lambda s: len(s) > 0)


class AddHostSchema(Schema):
    """
    validators for parameter of /host/addHost
    """
    domainName = fields.String(required=True, validate=lambda s: len(s) > 0)
    hostInfos = fields.List(fields.Nested(HostSchema(), required=True), required=True, validate=lambda s: len(s) > 0)


class DeleteHostSchema(Schema):
    """
    validators for parameter of /host/deleteHost
    """
    domainName = fields.String(required=True, validate=lambda s: len(s) > 0)
    hostInfos = fields.List(fields.Nested(SingleDeleteHostSchema(), required=True), required=True,
                            validate=lambda s: len(s) > 0)


class GetHostSchema(Schema):
    """
    validators for parameter of /host/getHost
    """
    domainName = fields.String(required=True, validate=lambda s: len(s) > 0)


class GetNonexistentDomainSchema(Schema):
    """
    validators for parameter of /conftrace/host/getNonexistentHost
    """
    clusterId = fields.String(required=True, validate=lambda s: len(s) > 0)
