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
@Time: 2024/5/27 10:02
@Author: JiaoSiMao
Description:
"""
import ast
import json
import os

from ragdoll.app import TARGETDIR, cache
from ragdoll.app.proxy.domain_host import DomainHostProxy
from ragdoll.app.serialize.domain_host import AddHostSchema, DeleteHostSchema, GetHostSchema, GetNonexistentDomainSchema
from ragdoll.app.utils.format import Format
from ragdoll.app.utils.git_tools import GitTools

from vulcanus.conf.constant import UserRoleType
from vulcanus.restful.resp.state import PARAM_ERROR, SUCCEED, PARTIAL_SUCCEED, SERVER_ERROR, DATABASE_QUERY_ERROR, \
    PERMESSION_ERROR, NO_DATA
from vulcanus.restful.response import BaseResponse
from vulcanus.log.log import LOGGER


class AddHostInDomain(BaseResponse):
    @BaseResponse.handle(schema=AddHostSchema, proxy=DomainHostProxy)
    def post(self, callback: DomainHostProxy, **params):
        """
        add host in the configuration domain

        add host in the configuration domain # noqa: E501

        :param body: domain info
        :type body: dict | bytes

        :rtype: BaseResponse
        """
        # 判断是否是管理员
        user_role = cache.user_role
        if not user_role:
            return self.response(code=DATABASE_QUERY_ERROR, message="Failed to query user permission information!")

        if user_role == UserRoleType.NORMAL:
            LOGGER.error("no user permission to add domain host")
            return self.response(code=PERMESSION_ERROR, message="no user permission to add domain host!")

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
        Format.addHostSyncStatus(domain, host_infos)

        # Check whether the current host exists in the domain.
        for host in host_infos:
            # 判断这个hostId是否在其他业务域中
            contained_flag = Format.isContainedHostIdInOtherDomain(host.get("hostId"))
            if contained_flag:
                failedHost.append(host.get("hostId"))
            else:
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

        # 添加host到表domain_host
        if successHost:
            # 过滤出添加成功的host
            filtered_host_infos = [info for info in host_infos if info.get("hostId") in successHost]
            result = callback.add_domain_hosts(domain, filtered_host_infos)
            if result != SUCCEED:
                LOGGER.error(f"add domain host {filtered_host_infos} error")
        return self.response(code=codeNum, message=codeString)


class DeleteHostInDomain(BaseResponse):
    @BaseResponse.handle(schema=DeleteHostSchema, proxy=DomainHostProxy)
    def delete(self, callback: DomainHostProxy, **params):
        """delete host in the configuration  domain

            delete the host in the configuration domain # noqa: E501

            :param body: domain info
            :type body: dict | bytes

            :rtype: BaseResponse
            """
        # 判断是否是管理员
        user_role = cache.user_role
        if not user_role:
            return self.response(code=DATABASE_QUERY_ERROR, message="Failed to query user permission information!")

        if user_role == UserRoleType.NORMAL:
            LOGGER.error("no user permission to delete domain host")
            return self.response(code=PERMESSION_ERROR, message="no user permission to delete domain host!")

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
        Format.deleteHostSyncStatus(domain, hostInfos)

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

        # 将host从表domain_host中删除
        if containedInHost:
            # 过滤出从文件中删除成功的host
            # 过滤出添加成功的host
            filtered_host_infos = [info for info in hostInfos if info.get("hostId") in containedInHost]
            result = callback.delete_domain_host(domain, filtered_host_infos)
            if result != SUCCEED:
                LOGGER.error(f"delete domain host {filtered_host_infos} error")
        return self.response(code=codeNum, message=codeString)


class GetHostByDomainName(BaseResponse):
    @BaseResponse.handle(schema=GetHostSchema, proxy=DomainHostProxy)
    def post(self, callback: DomainHostProxy, **params):
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

        # 从数据库中读取数据
        codeNum, hostlist = callback.get_domain_host_by_domain(domain)
        # Joining together the returned codeNum codeMessage
        if len(hostlist) == 0:
            return self.response(code=codeNum, message="Some unknown problems.")
        else:
            LOGGER.debug("hostlist is : {}".format(hostlist))
            return self.response(code=codeNum, message="Get host info in the domain successfully", data=hostlist)


class GetNonexistentDomainHost(BaseResponse):
    @BaseResponse.handle(schema=GetNonexistentDomainSchema, proxy=DomainHostProxy)
    def post(self, callback: DomainHostProxy, **params):
        """
            get not exist host

            get not exist host # noqa: E501

            :param body: domain info
            :type body: dict | bytes

            :rtype: List[Host]
        """
        clusterId = params.get("clusterId")
        # 获取集群下的所有主机
        cluster_host_list = Format.get_cluster_all_host(clusterId)
        if not cluster_host_list:
            return self.response(code=NO_DATA, message="No hosts are available in the current cluster")
        # 获取集群下的所有domain
        domain_id_list = Format.get_cluster_domain(clusterId)
        if not domain_id_list:
            return self.response(code=NO_DATA, message="No domain in the current cluster")
        # 获取domain下的所有已经添加的主机
        _, hostlist = callback.get_domain_host_by_domain_id_list(domain_id_list)
        if not hostlist:
            return self.response(code=SUCCEED, message="get host succeed", data=cluster_host_list)
        # 将集群下的所有主机与已添加的主机做对比过滤
        host_ids_set = {item["hostId"] for item in hostlist}
        filtered_items = [item for item in cluster_host_list if item["host_id"] not in host_ids_set]

        return self.response(code=SUCCEED, message="get host succeed", data=filtered_items)