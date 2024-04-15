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
@Time: 2024/3/5 9:40
@Author: JiaoSiMao
Description:
"""
import ast
import json
import os

from vulcanus.restful.resp.state import PARAM_ERROR, SUCCEED, PARTIAL_SUCCEED, SERVER_ERROR
from vulcanus.restful.response import BaseResponse

from ragdoll.conf.constant import TARGETDIR
from ragdoll.function.verify.host import AddHostSchema, DeleteHostSchema, GetHostSchema
from ragdoll.log.log import LOGGER
from ragdoll.utils.conf_tools import ConfTools
from ragdoll.utils.format import Format
from ragdoll.utils.git_tools import GitTools


class AddHostInDomain(BaseResponse):
    @BaseResponse.handle(schema=AddHostSchema, token=True)
    def post(self, **params):
        """
        add host in the configuration domain

        add host in the configuration domain # noqa: E501

        :param body: domain info
        :type body: dict | bytes

        :rtype: BaseResponse
        """

        domain = params.get("domainName")
        host_infos = params.get("hostInfos")

        # check whether host_infos is empty
        if len(host_infos) == 0:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum, message="Enter host info cannot be empty, please check the host info.")

        checkRes = Format.domainCheck(domain)
        if not checkRes:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum,
                                 message="Failed to verify the input parameter, please check the input parameters.")

        # check whether the domain exists
        isExist = Format.isDomainExist(domain)
        if not isExist:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum,
                                 message="The current domain does not exist, please create the domain first.")

        successHost = []
        failedHost = []
        domainPath = os.path.join(TARGETDIR, domain)
        # 将domainName 和host信息入库
        conf_tools = ConfTools()
        Format.addHostSyncStatus(conf_tools, domain, host_infos)

        # Check whether the current host exists in the domain.
        for host in host_infos:
            hostPath = os.path.join(domainPath, "hostRecord.txt")
            if os.path.isfile(hostPath):
                isContained = Format.isContainedHostIdInfile(hostPath, host.get("hostId"))
                if isContained:
                    failedHost.append(host.get("hostId"))
                else:
                    Format.addHostToFile(hostPath, host)
                    successHost.append(host.get("hostId"))
            else:
                Format.addHostToFile(hostPath, host)
                successHost.append(host.get("hostId"))

        if len(failedHost) == len(host_infos):
            codeNum = PARAM_ERROR
            return self.response(code=codeNum,
                                 message="The all host already exists in the administrative scope of the domain.")

        # Joining together the returned codenum codeMessage
        if len(failedHost) == 0:
            codeNum = SUCCEED
            codeString = Format.spliceAllSuccString("host", "add hosts", successHost)
        else:
            codeNum = PARTIAL_SUCCEED
            codeString = Format.splicErrorString("host", "add hosts", successHost, failedHost)

        # git commit maessage
        if len(host_infos) > 0:
            git_tools = GitTools()
            commit_code = git_tools.gitCommit("Add the host in {} domian, ".format(domain) +
                                              "the host including : {}".format(successHost))

        return self.response(code=codeNum, message=codeString)


class DeleteHostInDomain(BaseResponse):
    @BaseResponse.handle(schema=DeleteHostSchema, token=True)
    def delete(self, **params):
        """delete host in the configuration  domain

            delete the host in the configuration domain # noqa: E501

            :param body: domain info
            :type body: dict | bytes

            :rtype: BaseResponse
            """
        domain = params.get("domainName")
        hostInfos = params.get("hostInfos")

        # check the input domain
        checkRes = Format.domainCheck(domain)
        if not checkRes:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum,
                                 message="Failed to verify the input parameter, please check the input parameters.")

        #  check whether the domain exists
        isExist = Format.isDomainExist(domain)
        if not isExist:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum,
                                 message="The current domain does not exist, please create the domain first.")

        # 将host sync status从库中删除
        conf_tools = ConfTools()
        Format.deleteHostSyncStatus(conf_tools, domain, hostInfos)

        # Whether the host information added within the current domain is empty while ain exists
        domainPath = os.path.join(TARGETDIR, domain)
        hostPath = os.path.join(domainPath, "hostRecord.txt")
        if not os.path.isfile(hostPath) or (os.path.isfile(hostPath) and os.stat(hostPath).st_size == 0):
            codeNum = PARAM_ERROR
            return self.response(code=codeNum,
                                 message="The host information is not set in the current domain. Please add the host "
                                         "information first")

            # If the input host information is empty, the host information of the whole domain is cleared
        if len(hostInfos) == 0:
            if os.path.isfile(hostPath):
                try:
                    os.remove(hostPath)
                except OSError as ex:
                    LOGGER.error("Failed to delete hostpath as OS error: {0}".format(ex))
                    codeNum = SERVER_ERROR
                    return self.response(code=codeNum, message="The host delete failed.")
                codeNum = SUCCEED
                return self.response(code=codeNum, message="All hosts are deleted in the current domain.")

        # If the domain exists, check whether the current input parameter host belongs to the corresponding
        # domain. If the host is in the domain, the host is deleted. If the host is no longer in the domain,
        # the host is added to the failure range
        containedInHost = []
        notContainedInHost = []
        os.umask(0o077)
        for hostInfo in hostInfos:
            hostId = hostInfo.get("hostId")
            isContained = False
            try:
                with open(hostPath, 'r') as d_file:
                    lines = d_file.readlines()
                    with open(hostPath, 'w') as w_file:
                        for line in lines:
                            line_host_id = json.loads(str(ast.literal_eval(line)).replace("'", "\""))['host_id']
                            if hostId != line_host_id:
                                w_file.write(line)
                            else:
                                isContained = True
            except OSError as err:
                LOGGER.error("OS error: {0}".format(err))
                codeNum = SERVER_ERROR
                return self.response(code=codeNum, message="OS error: {0}".format(err))

            if isContained:
                containedInHost.append(hostId)
            else:
                notContainedInHost.append(hostId)

        # All hosts do not belong to the domain
        if len(notContainedInHost) == len(hostInfos):
            codeNum = PARAM_ERROR
            return self.response(code=codeNum,
                                 message="All the host does not belong to the domain control, please enter the host "
                                         "again")

            # Some hosts belong to domains, and some hosts do not belong to domains.
        if len(notContainedInHost) == 0:
            codeNum = SUCCEED
            codeString = Format.spliceAllSuccString("host", "delete", containedInHost)
        else:
            codeNum = PARAM_ERROR
            codeString = Format.splicErrorString("host", "delete", containedInHost, notContainedInHost)

        # git commit message
        if len(containedInHost) > 0:
            git_tools = GitTools()
            commit_code = git_tools.gitCommit("Delete the host in {} domian, ".format(domain) +
                                              "the host including : {}".format(containedInHost))

        return self.response(code=codeNum, message=codeString)


class GetHostByDomainName(BaseResponse):
    @BaseResponse.handle(schema=GetHostSchema, token=True)
    def post(self, **params):
        """get host by domainName

            get the host information of the configuration domain # noqa: E501

            :param body: domain info
            :type body: dict | bytes

            :rtype: List[Host]
            """
        domain = params.get("domainName")
        # check the input domain
        checkRes = Format.domainCheck(domain)
        if not checkRes:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum,
                                 message="Failed to verify the input parameter, please check the input parameters.")

        #  check whether the domain exists
        isExist = Format.isDomainExist(domain)
        if not isExist:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum,
                                 message="The current domain does not exist, please create the domain first.")

        # The domain exists, but the host information is empty
        domainPath = os.path.join(TARGETDIR, domain)
        hostPath = os.path.join(domainPath, "hostRecord.txt")
        if not os.path.isfile(hostPath) or (os.path.isfile(hostPath) and os.stat(hostPath).st_size == 0):
            codeNum = PARAM_ERROR
            return self.response(code=codeNum,
                                 message="The host information is not set in the current domain. Please add the host "
                                         "information first.")

            # The domain exists, and the host information exists and is not empty
        hostlist = []
        LOGGER.debug("hostPath is : {}".format(hostPath))
        try:
            with open(hostPath, 'r') as d_file:
                for line in d_file.readlines():
                    json_str = json.loads(line)
                    host_json = ast.literal_eval(json_str)
                    hostId = host_json["host_id"]
                    ip = host_json["ip"]
                    ipv6 = host_json["ipv6"]
                    host = {"hostId": hostId, "ip": ip, "ipv6": ipv6}
                    hostlist.append(host)
        except OSError as err:
            LOGGER.error("OS error: {0}".format(err))
            codeNum = SERVER_ERROR
            return self.response(code=codeNum, message="OS error: {0}".format(err))

        # Joining together the returned codeNum codeMessage
        if len(hostlist) == 0:
            codeNum = SERVER_ERROR
            return self.response(code=codeNum, message="Some unknown problems.")
        else:
            LOGGER.debug("hostlist is : {}".format(hostlist))
            codeNum = SUCCEED
            return self.response(code=codeNum, message="Get host info in the domain successfully", data=hostlist)
