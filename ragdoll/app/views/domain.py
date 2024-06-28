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
@FileName: view.py
@Time: 2024/3/4 10:34
@Author: JiaoSiMao
Description:
"""
import os
import shutil

from ragdoll.app import TARGETDIR, cache
from ragdoll.app.proxy.domain import DomainProxy
from ragdoll.app.serialize.domain import CreateDomainSchema, DeleteDomainSchema, GetDomainsPage_RequestSchema
from ragdoll.app.utils.format import Format

from vulcanus.conf.constant import UserRoleType
from vulcanus.log.log import LOGGER
from vulcanus.restful.resp.state import SUCCEED, SERVER_ERROR, PARAM_ERROR, DATABASE_QUERY_ERROR, PERMESSION_ERROR
from vulcanus.restful.response import BaseResponse


class CreateDomain(BaseResponse):

    @BaseResponse.handle(schema=CreateDomainSchema, proxy=DomainProxy)
    def post(self, callback: DomainProxy, **params):
        """
        create domain

        Args:
            args (dict): e.g
            {
                "domainName":"xxx",
                "priority":""
            }

        Returns:
            dict: response body
        """
        # 判断是否是管理员
        user_role = cache.user_role
        if not user_role:
            return self.response(code=DATABASE_QUERY_ERROR, message="Failed to query user permission information!")

        if user_role == UserRoleType.NORMAL:
            LOGGER.error("no user permission to create domain")
            return self.response(code=PERMESSION_ERROR, message="no user permission to create domain!")

        successDomain = []
        failedDomain = []
        tempDomainName = params.get("domainName")
        checkRes = Format.domainCheck(tempDomainName)
        isExist = Format.isDomainExist(tempDomainName)

        if isExist or not checkRes:
            failedDomain.append(tempDomainName)
        else:
            successDomain.append(tempDomainName)
            domainPath = os.path.join(TARGETDIR, tempDomainName)
            os.umask(0o077)
            os.makedirs(domainPath)

        codeString = ""
        if len(failedDomain) == 0:
            codeNum = SUCCEED
            codeString = Format.spliceAllSuccString("domain", "created", successDomain)
        else:
            codeNum = SERVER_ERROR
            if params:
                if isExist:
                    codeString = "domain {} create failed because it has been existed.".format(failedDomain[0])
                elif not checkRes:
                    codeString = "domain {} create failed because format is incorrect.".format(failedDomain[0])
            else:
                codeString = Format.splicErrorString("domain", "created", successDomain, failedDomain)
        # 将domain数据添加到domain表
        if successDomain:
            domain_info = {"domain_name": tempDomainName, "cluster_id": params.get("clusterId")}
            result = callback.add_domain(domain_info)
            if result != SUCCEED:
                LOGGER.error(f"add domain {tempDomainName} error")
        return self.response(code=codeNum, message=codeString)


class DeleteDomain(BaseResponse):

    @BaseResponse.handle(schema=DeleteDomainSchema, proxy=DomainProxy)
    def delete(self, callback: DomainProxy, **params):
        # 判断是否是管理员
        user_role = cache.user_role
        if not user_role:
            return self.response(code=DATABASE_QUERY_ERROR, message="Failed to query user permission information!")

        if user_role == UserRoleType.NORMAL:
            LOGGER.error("no user permission to delete domain")
            return self.response(code=PERMESSION_ERROR, message="no user permission to delete domain!")

        domainName = params.get("domainName")

        if not domainName:
            codeString = "The entered domain is empty"
            return self.response(code=PARAM_ERROR, message=codeString)

        successDomain = []
        failedDomain = []

        checkRes = Format.domainCheck(domainName)
        isExist = Format.isDomainExist(domainName)
        if checkRes and isExist:
            domainPath = os.path.join(TARGETDIR, domainName)
            successDomain.append(domainName)
            shutil.rmtree(domainPath)
        else:
            failedDomain.append(domainName)

        if len(failedDomain) == 0:
            codeNum = SUCCEED
            codeString = Format.spliceAllSuccString("domain", "delete", successDomain)
        else:
            codeNum = SERVER_ERROR
            codeString = Format.splicErrorString("domain", "delete", successDomain, failedDomain)
        # 将domain数据从domain表中删除
        if successDomain:
            result = callback.delete_domain(params.get("domainId"))
            if result != SUCCEED:
                LOGGER.error(f"delete domain {domainName} error")
        return self.response(code=codeNum, message=codeString)


class QueryDomain(BaseResponse):
    @BaseResponse.handle(schema=GetDomainsPage_RequestSchema, proxy=DomainProxy)
    def post(self, callback: DomainProxy, **params):
        # 判断是否是管理员
        user_role = cache.user_role
        if not user_role:
            return self.response(code=DATABASE_QUERY_ERROR, message="Failed to query user permission information!")

        if user_role == UserRoleType.NORMAL:
            # 如果没有传入筛选值或者传入的筛选值不在允许查看的集群范围内，就按照允许查看的集群范围显示业务域
            if not params.get("cluster_list") or Format.is_not_in_clusters(params.get("cluster_list"),
                                                                           cache.get_user_clusters().keys()):
                params["cluster_list"] = cache.get_user_clusters().keys()

        code_num, domains_result = callback.get_domains(params)
        # 根据cluster_id查询cluster_name
        for domain_info in domains_result["domain_infos"]:
            cluster_id = domain_info["cluster_id"]
            cluster = cache.clusters.get(cluster_id)
            domain_info["cluster_name"] = cluster["cluster_name"]
        return self.response(code=code_num, data=domains_result)
