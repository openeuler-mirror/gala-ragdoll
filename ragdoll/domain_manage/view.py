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

from vulcanus.restful.resp.state import SUCCEED, SERVER_ERROR, PARAM_ERROR
from vulcanus.restful.response import BaseResponse

from ragdoll.conf.constant import TARGETDIR
from ragdoll.function.verify.domain import CreateDomainSchema, DeleteDomainSchema
from ragdoll.utils.format import Format
from ragdoll.utils.git_tools import GitTools


class CreateDomain(BaseResponse):

    @BaseResponse.handle(schema=CreateDomainSchema, token=True)
    def post(self, **params):
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
        print("create domain")
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
            os.mkdir(domainPath)

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

        return self.response(code=codeNum, message=codeString)


class DeleteDomain(BaseResponse):

    @BaseResponse.handle(schema=DeleteDomainSchema, token=True)
    def delete(self, **params):
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

        return self.response(code=codeNum, message=codeString)


class QueryDomain(BaseResponse):
    @BaseResponse.handle(token=True)
    def post(self, **params):
        domain_list = []
        cmd = "ls {}".format(TARGETDIR)
        gitTools = GitTools()
        ls_res = gitTools.run_shell_return_output(cmd).decode()
        ll_list = ls_res.split('\n')
        for d_ll in ll_list:
            if d_ll:
                domain = {"domainName": d_ll}
                domain_list.append(domain)
        return self.response(code=SUCCEED, data=domain_list)
