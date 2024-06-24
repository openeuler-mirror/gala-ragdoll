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
@FileName: confs.py
@Time: 2024/3/11 9:02
@Author: JiaoSiMao
Description:
"""
from marshmallow import Schema, fields


class DomainNameSchema(Schema):
    domainName = fields.String(required=True, validate=lambda s: len(s) > 0)


class HostIdSchema(Schema):
    hostId = fields.Integer(required=True, validate=lambda s: s >= 0)


class SyncHostConfsSchema(Schema):
    hostId = fields.Integer(required=True, validate=lambda s: s >= 0)
    syncConfigs = fields.List(fields.String(required=True, validate=lambda s: len(s) > 0), required=True,
                              validate=lambda s: len(s) > 0)


class ConfBaseSchema(Schema):
    filePath = fields.String(required=True, validate=lambda s: len(s) > 0)
    expectedContents = fields.String(required=True, validate=lambda s: len(s) > 0)


class DomainConfBaseInfosSchema(Schema):
    domainName = fields.String(required=True, validate=lambda s: len(s) > 0)
    confBaseInfos = fields.List(fields.Nested(ConfBaseSchema(), required=True), required=True,
                                validate=lambda s: len(s) > 0)


class GetSyncStatusSchema(Schema):
    domainName = fields.String(required=True, validate=lambda s: len(s) > 0)
    ip = fields.String(required=True, validate=lambda s: len(s) > 0)


class QueryExceptedConfsSchema(Schema):
    domainNames = fields.List(fields.Nested(DomainNameSchema(), required=True), required=True,
                              validate=lambda s: len(s) > 0)


class QueryRealConfsSchema(Schema):
    domainName = fields.String(required=True, validate=lambda s: len(s) > 0)
    hostIds = fields.List(fields.Nested(HostIdSchema(), required=True), required=True,
                          validate=lambda s: len(s) > 0)


class SyncConfToHostFromDomainSchema(Schema):
    domainName = fields.String(required=True, validate=lambda s: len(s) > 0)
    syncList = fields.List(fields.Nested(SyncHostConfsSchema(), required=True), required=True,
                           validate=lambda s: len(s) > 0)


class QuerySupportedConfsSchema(Schema):
    domainName = fields.String(required=True, validate=lambda s: len(s) > 0)


class CompareConfDiffSchema(Schema):
    expectedConfsResp = fields.List(fields.Nested(DomainConfBaseInfosSchema(), required=True), required=True,
                                    validate=lambda s: len(s) > 0)
    domainResult = fields.Dict(required=True, validate=lambda s: len(s) > 0)


class BatchSyncConfToHostFromDomainSchema(Schema):
    domainName = fields.String(required=True, validate=lambda s: len(s) > 0)
    hostIds = fields.List(fields.Integer(required=True, validate=lambda s: s >= 0), required=True,
                          validate=lambda s: len(s) > 0)
