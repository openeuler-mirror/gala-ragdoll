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
@FileName: domain_conf_info.py
@Time: 2024/3/8 11:40
@Author: JiaoSiMao
Description:
"""
from marshmallow import Schema, fields


class ConfSchema(Schema):
    filePath = fields.String(required=False, validate=lambda s: len(s) > 0)
    contents = fields.String(required=False, validate=lambda s: len(s) > 0)
    hostId = fields.String(required=False, validate=lambda s: len(s) > 0)


class ManageConfSchema(Schema):
    filePath = fields.String(required=False, validate=lambda s: len(s) > 0)


class AddManagementConfsSchema(Schema):
    domainName = fields.String(required=True, validate=lambda s: len(s) > 0)
    confFiles = fields.List(fields.Nested(ConfSchema(), required=True), required=True, validate=lambda s: len(s) > 0)


class DeleteManagementConfsSchema(Schema):
    domainName = fields.String(required=True, validate=lambda s: len(s) > 0)
    confFiles = fields.List(fields.Nested(ManageConfSchema(), required=True), required=True,
                            validate=lambda s: len(s) > 0)


class GetManagementConfsSchema(Schema):
    domainName = fields.String(required=True, validate=lambda s: len(s) > 0)


class QueryChangelogSchema(Schema):
    domainName = fields.String(required=True, validate=lambda s: len(s) > 0)
    confFiles = fields.List(fields.Nested(ManageConfSchema(), required=True), required=True,
                            validate=lambda s: len(s) > 0)
