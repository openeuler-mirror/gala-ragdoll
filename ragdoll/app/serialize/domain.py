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
@FileName: domain.py
@Time: 2024/3/4 10:48
@Author: JiaoSiMao
Description:
"""
from marshmallow import Schema, fields, validate

from ragdoll.database import Domain


class CreateDomainSchema(Schema):
    """
    validators for parameter of /domain/createDomain
    """
    domainName = fields.String(required=True, validate=lambda s: len(s) > 0)
    clusterId = fields.String(required=True, validate=lambda s: len(s) > 0)
    priority = fields.Integer(required=True, validate=lambda s: s >= 0)


class DeleteDomainSchema(Schema):
    """
    validators for parameter of /domain/deleteDomain
    """
    domainName = fields.String(required=True, validate=lambda s: len(s) > 0)
    domainId = fields.String(required=True, validate=lambda s: len(s) > 0)


class GetDomainsPage_RequestSchema(Schema):
    cluster_list = fields.List(fields.String(required=False), required=False, missing=None)
    sort = fields.String(required=False, missing=None, validate=validate.OneOf(["domain_id", "domain_name", ""]))
    direction = fields.String(required=False, missing=None, validate=validate.OneOf(["desc", "asc"]))
    page = fields.Integer(required=False, missing=None, validate=lambda s: s > 0)
    per_page = fields.Integer(required=False, missing=None, validate=lambda s: 50 > s > 0)


class GetDomainsPage_ResponseSchema(Schema):
    cluster_name = fields.String(required=False, missing=None, validate=lambda s: 50 >= len(s) > 0)

    class Meta:
        model = Domain
        fields = (
            "domain_id",
            "domain_name",
            "cluster_id",
            "priority",
        )
