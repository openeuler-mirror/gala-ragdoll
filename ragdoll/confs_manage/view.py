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
@Time: 2024/3/11 9:01
@Author: JiaoSiMao
Description:
"""
import os

import connexion
from vulcanus.restful.resp.state import SUCCEED, SERVER_ERROR, PARAM_ERROR, NO_DATA
from vulcanus.restful.response import BaseResponse

from ragdoll.conf.constant import TARGETDIR
from ragdoll.const.conf_files import yang_conf_list
from ragdoll.const.conf_handler_const import NOT_SYNCHRONIZE
from ragdoll.function.verify.confs import GetSyncStatusSchema, QueryExceptedConfsSchema, QueryRealConfsSchema, \
    SyncConfToHostFromDomainSchema, QuerySupportedConfsSchema, CompareConfDiffSchema, \
    BatchSyncConfToHostFromDomainSchema
from ragdoll.log.log import LOGGER
from ragdoll.utils.conf_tools import ConfTools
from ragdoll.utils.format import Format
from ragdoll.utils.host_tools import HostTools
from ragdoll.utils.yang_module import YangModule


class GetTheSyncStatusOfDomain(BaseResponse):
    @BaseResponse.handle(schema=GetSyncStatusSchema, token=True)
    def post(self, **params):
        """
            get the status of the domain
            get the status of whether the domain has been synchronized # noqa: E501

            :param body:
            :type body: dict | bytes

            :rtype: SyncStatus
            """
        access_token = connexion.request.headers.get("access_token")
        domain = params.get("domainName")
        ip = params.get("ip")
        # check domain
        base_rsp, code_num = Format.check_domain_param(domain)
        if code_num != 200:
            return base_rsp, code_num

        # get manage confs in domain
        code_num, code_string, manage_confs = Format.get_domain_conf(domain)
        if not manage_confs:
            return self.response(code=SUCCEED, message=code_string, data=manage_confs)

        # get real conf in host
        host_id = Format.get_host_id_by_ip(ip, domain)
        real_conf_res_text = Format.get_realconf_by_domain_and_host(domain, [host_id], access_token)
        if real_conf_res_text is None:
            return self.response(code=SERVER_ERROR, message="get real conf failed")

        # compare manage conf with real conf
        sync_status = Format.diff_mangeconf_with_realconf(domain, real_conf_res_text, manage_confs)

        # deal with not found files
        man_conf_list = []
        for d_man_conf in manage_confs:
            man_conf_list.append(d_man_conf.get("file_path").split(":")[-1])
        for d_host in sync_status["hostStatus"]:
            d_sync_status = d_host["syncStatus"]
            file_list = []
            for d_file in d_sync_status:
                file_path = d_file["file_path"]
                file_list.append(file_path)
            for d_man_conf in man_conf_list:
                if d_man_conf in file_list:
                    continue
                else:
                    comp_res = "NOT FOUND"
                    conf_is_synced = {"file_path": d_man_conf, "isSynced": comp_res}
                    d_sync_status.append(conf_is_synced)
        return self.response(code=SUCCEED, message="successfully get the sync status of domain", data=sync_status)


class QueryExceptedConfs(BaseResponse):
    @BaseResponse.handle(schema=QueryExceptedConfsSchema, token=True)
    def post(self, **params):
        """
            query the supported configurations in the current project
            queryExpectedConfs # noqa: E501

            :rtype: List[ExceptedConfInfo]
            """
        # 直接从入参中读取domain列表
        domain_names = params.get("domainNames")
        if len(domain_names) == 0:
            code_num = PARAM_ERROR
            code_string = "The current domain does not exist, please create the domain first."
            return self.response(code=code_num, message=code_string)

        all_domain_expected_files = []
        yang_modules = YangModule()
        for d_domain in domain_names:
            domain_path = os.path.join(TARGETDIR, d_domain["domainName"])
            expected_conf_lists = {"domainName": d_domain["domainName"], "confBaseInfos": []}
            # Traverse all files in the source management repository
            for root, dirs, files in os.walk(domain_path):
                # Domain also contains host cache files, so we need to add hierarchical judgment for root
                if len(files) > 0 and len(root.split('/')) > 3:
                    if "hostRecord.txt" in files:
                        continue
                    for d_file in files:
                        feature = os.path.join(root.split('/')[-1], d_file)
                        d_module = yang_modules.getModuleByFeature(feature)
                        file_lists = yang_modules.getFilePathInModdule(yang_modules.module_list)
                        file_path = file_lists.get(d_module.name()).split(":")[-1]
                        d_file_path = os.path.join(root, d_file)
                        expected_value = Format.get_file_content_by_read(d_file_path)
                        conf_base_info = {"filePath": file_path, "expectedContents": expected_value}
                        expected_conf_lists.get("confBaseInfos").append(conf_base_info)
            all_domain_expected_files.append(expected_conf_lists)

        LOGGER.debug("all_domain_expected_files is : {}".format(all_domain_expected_files))

        if len(all_domain_expected_files) == 0:
            code_num = PARAM_ERROR
            code_string = "The current domain does not exist, please create the domain first."
            return self.response(code=code_num, message=code_string)

        return self.response(code=SUCCEED, message="Successfully get the expected configuration file information.",
                             data=all_domain_expected_files)


class QueryRealConfs(BaseResponse):
    @BaseResponse.handle(schema=QueryRealConfsSchema, token=True)
    def post(self, **params):
        """
        query the real configuration value in the current hostId node

        query the real configuration value in the current hostId node # noqa: E501

        :param body:
        :type body: dict | bytes

        :rtype: List[RealConfInfo]
        """
        access_token = connexion.request.headers.get("access_token")
        domain = params.get("domainName")
        host_list = params.get("hostIds")

        check_res = Format.domainCheck(domain)
        if not check_res:
            codeNum = PARAM_ERROR
            codeString = "Failed to verify the input parameter, please check the input parameters."
            return self.response(code=codeNum, message=codeString)

        # check the domain is Exist
        is_exist = Format.isDomainExist(domain)
        if not is_exist:
            codeNum = PARAM_ERROR
            codeString = "The current domain does not exist, please create the domain first."
            return self.response(code=codeNum, message=codeString)

        # check whether the host is configured in the domain
        is_host_list_exist = Format.isHostInDomain(domain)
        LOGGER.debug("is_host_list_exist is : {}".format(is_host_list_exist))
        if not is_host_list_exist:
            codeNum = PARAM_ERROR
            codeString = "The host information is not set in the current domain. Please add the host information first"
            return self.response(code=codeNum, message=codeString)

        # get all hosts managed by the current domain.
        # If host_list is empty, query all hosts in the current domain.
        # If host_list is not empty, the actual contents of the currently given host are queried.
        exist_host = []
        failed_host = []
        if len(host_list) > 0:
            host_tool = HostTools()
            exist_host, failed_host = host_tool.getHostExistStatus(domain, host_list)
        else:
            res_text = Format.get_hostinfo_by_domain(domain)
            if len(res_text) == 0:
                code_num = NO_DATA
                code_string = "The host currently controlled in the domain is empty. Please add host information to " \
                              "the domain. "
                return self.response(code=code_num, message=code_string)

        if len(exist_host) == 0 or len(failed_host) == len(host_list):
            codeNum = PARAM_ERROR
            codeString = "The host information is not set in the current domain. Please add the host information first"
            return self.response(code=codeNum, message=codeString)

        # get the management conf in domain
        res = Format.get_realconf_by_domain_and_host(domain, exist_host, access_token)
        if len(res) == 0:
            codeNum = NO_DATA
            codeString = "Real configuration query failed. The failure reason is : The real configuration does not " \
                         "found. "
            return self.response(code=codeNum, message=codeString)

        return self.response(code=SUCCEED, message="Successfully query real confs", data=res)


class SyncConfToHostFromDomain(BaseResponse):
    @BaseResponse.handle(schema=SyncConfToHostFromDomainSchema, token=True)
    def put(self, **params):
        """
            synchronize the configuration information of the configuration domain to the host # noqa: E501

            :param body:
            :type body: dict | bytes

            :rtype: List[HostSyncResult]
            """
        access_token = connexion.request.headers.get("access_token")
        domain = params.get("domainName")
        sync_list = params.get("syncList")

        host_sync_confs = dict()

        for sync in sync_list:
            host_sync_confs[sync["hostId"]] = sync["syncConfigs"]

        # check the input domain
        check_res = Format.domainCheck(domain)
        if not check_res:
            code_num = PARAM_ERROR
            code_string = "Failed to verify the input parameter, please check the input parameters."
            return self.response(code=code_num, message=code_string)

        #  check whether the domain exists
        is_exist = Format.isDomainExist(domain)
        if not is_exist:
            code_num = NO_DATA
            code_string = "The current domain does not exist, please create the domain first."
            return self.response(code=code_num, message=code_string)

        # get the management host in domain
        res_host_text = Format.get_hostinfo_by_domain(domain)
        if len(res_host_text) == 0:
            code_num = NO_DATA
            code_string = "The host currently controlled in the domain is empty. Please add host information to the " \
                          "domain. "
            return self.response(code=code_num, message=code_string)

        # Check whether the host is in the managed host list
        exist_host = []
        if len(host_sync_confs) > 0:
            host_ids = host_sync_confs.keys()
            for host_id in host_ids:
                for d_host in res_host_text:
                    if host_id == d_host.get("host_id"):
                        exist_host.append(host_id)
        else:
            for d_host in res_host_text:
                temp_host = {}
                temp_host["hostId"] = d_host.get("host_id")
                exist_host.append(temp_host)
        LOGGER.debug("exist_host is : {}".format(exist_host))

        if len(exist_host) == 0:
            code_num = PARAM_ERROR
            code_string = "The host information is not set in the current domain. Please add the host information first"
            return self.response(code=code_num, message=code_string)

        # get the management conf in domain
        man_conf_res_text = Format.get_manageconf_by_domain(domain)
        LOGGER.debug("man_conf_res_text is : {}".format(man_conf_res_text))
        manage_confs = man_conf_res_text.get("conf_files")

        # Deserialize and reverse parse the expected configuration
        conf_tools = ConfTools()
        # 组装入参
        file_path_infos = dict()
        for host_id in exist_host:
            sync_confs = host_sync_confs.get(host_id)
            for d_man_conf in manage_confs:
                file_path = d_man_conf.get("file_path").split(":")[-1]
                if file_path in sync_confs:
                    contents = d_man_conf.get("contents")
                    file_path_infos[file_path] = contents

        code_num, code_string, sync_res = Format.deal_batch_sync_res(conf_tools, exist_host, file_path_infos,
                                                                     access_token)
        if code_num != 200:
            return self.response(code=SERVER_ERROR, message=code_string, data=sync_res)
        return self.response(code=SUCCEED, message=code_string, data=sync_res)


class QuerySupportedConfs(BaseResponse):
    @BaseResponse.handle(schema=QuerySupportedConfsSchema, token=True)
    def post(self, **params):
        """
            query supported configuration list # noqa: E501

           :param body:
           :type body: dict | bytes

           :rtype: List
        """
        domain = params.get("domainName")
        check_res = Format.domainCheck(domain)
        if not check_res:
            code_num = PARAM_ERROR
            code_string = "Failed to verify the input parameter, please check the input parameters."
            return self.response(code=code_num, message=code_string)

        is_exist = Format.isDomainExist(domain)
        if not is_exist:
            code_num = NO_DATA
            code_string = "The current domain does not exist, please create the domain first."
            return self.response(code=code_num, message=code_string)

        conf_files = Format.get_manageconf_by_domain(domain)
        conf_files = conf_files.get("conf_files")
        if len(conf_files) == 0:
            return yang_conf_list

        exist_conf_list = []
        for conf in conf_files:
            exist_conf_list.append(conf.get('file_path'))

        return list(set(yang_conf_list).difference(set(exist_conf_list)))


class CompareConfDiff(BaseResponse):
    @BaseResponse.handle(schema=CompareConfDiffSchema, token=True)
    def post(self, **params):
        """
            compare conf different, return host sync status

            :param body:
            :type body: dict

            :rtype:
            """
        expected_confs_resp_list = params.get("expectedConfsResp")
        domain_result = params.get("domainResult")
        expected_confs_resp_dict = Format.deal_expected_confs_resp(expected_confs_resp_list)

        real_conf_res_text_dict = Format.deal_domain_result(domain_result)
        # 循环real_conf_res_text_list 取出每一个domain的domain_result与expected_confs_resp_dict的expected_confs_resp做对比
        sync_result = []
        for domain_name, real_conf_res_text_list in real_conf_res_text_dict.items():
            expected_confs_resp = expected_confs_resp_dict.get(domain_name)
            sync_status = Format.diff_mangeconf_with_realconf_for_db(domain_name, real_conf_res_text_list,
                                                                     expected_confs_resp)
            domain_name = sync_status["domainName"]
            host_status_list = sync_status["hostStatus"]

            for signal_status in host_status_list:
                host_id = signal_status["hostId"]
                domain_host_sync_status = 1
                sync_status_list = signal_status["syncStatus"]
                for single_sync_status in sync_status_list:
                    if single_sync_status["isSynced"] == NOT_SYNCHRONIZE:
                        domain_host_sync_status = 0
                        break
                single_domain_host_status = {"domain_name": domain_name, "host_id": host_id,
                                             "sync_status": domain_host_sync_status}
                sync_result.append(single_domain_host_status)
        return self.response(code=SUCCEED, message="successfully compare conf diff", data=sync_result)


class BatchSyncConfToHostFromDomain(BaseResponse):
    @BaseResponse.handle(schema=BatchSyncConfToHostFromDomainSchema, token=True)
    def put(self, **params):
        """
            synchronize the configuration information of the configuration domain to the host # noqa: E501

            :param body:
            :type body: dict | bytes

            :rtype: List[HostSyncResult]
            """
        access_token = connexion.request.headers.get("access_token")
        domain = params.get("domainName")
        host_ids = params.get("hostIds")
        # check domain
        base_rsp, code_num = Format.check_domain_param(domain)
        if code_num != 200:
            return base_rsp, code_num

        # 根据domain和ip获取有哪些不同步的文件
        # get manage confs in domain
        code_num, code_string, manage_confs = Format.get_domain_conf(domain)
        if not manage_confs:
            return self.response(code=SUCCEED, message=code_string, data=manage_confs)

        # get real conf in host
        real_conf_res_text = Format.get_realconf_by_domain_and_host(domain, host_ids, access_token)
        # compare manage conf with real conf
        sync_status = Format.diff_mangeconf_with_realconf(domain, real_conf_res_text, manage_confs)
        # 解析sync_status，取出未同步的数据
        host_sync_confs = dict()
        host_status = sync_status["hostStatus"]
        for host_result in host_status:
            host_id = host_result["hostId"]
            sync_status = host_result["syncStatus"]
            sync_configs = []
            for sync_result in sync_status:
                if sync_result["isSynced"] == NOT_SYNCHRONIZE:
                    sync_configs.append(sync_result["file_path"])
            host_sync_confs[host_id] = sync_configs

        # check the input domain
        check_res = Format.domainCheck(domain)
        if not check_res:
            code_num = PARAM_ERROR
            code_string = "Failed to verify the input parameter, please check the input parameters."
            return self.response(code=code_num, message=code_string)

        #  check whether the domain exists
        is_exist = Format.isDomainExist(domain)
        if not is_exist:
            code_num = NO_DATA
            code_string = "The current domain does not exist, please create the domain first."
            return self.response(code=code_num, message=code_string)

        # get the management host in domain
        res_host_text = Format.get_hostinfo_by_domain(domain)
        if len(res_host_text) == 0:
            code_num = NO_DATA
            code_string = "The host currently controlled in the domain is empty. Please add host information to the " \
                          "domain. "
            return self.response(code=code_num, message=code_string)
        # Check whether the host is in the managed host list
        exist_host = []
        if len(host_sync_confs) > 0:
            host_ids = host_sync_confs.keys()
            for host_id in host_ids:
                for d_host in res_host_text:
                    if host_id == d_host.get("host_id"):
                        exist_host.append(host_id)
        else:
            for d_host in res_host_text:
                tmp_host = {"hostId": d_host.get("host_id")}
                exist_host.append(tmp_host)
        LOGGER.debug("exist_host is : {}".format(exist_host))

        if len(exist_host) == 0:
            code_num = PARAM_ERROR
            code_string = "The host information is not set in the current domain. Please add the host information first"
            return self.response(code=code_num, message=code_string)

        # get the management conf in domain
        man_conf_res_text = Format.get_manageconf_by_domain(domain)
        LOGGER.debug("man_conf_res_text is : {}".format(man_conf_res_text))
        manage_confs = man_conf_res_text.get("conf_files")

        # Deserialize and reverse parse the expected configuration
        conf_tools = ConfTools()
        # 组装入参
        file_path_infos = dict()
        for host_id in exist_host:
            sync_confs = host_sync_confs.get(host_id)
            for d_man_conf in manage_confs:
                file_path = d_man_conf.get("file_path").split(":")[-1]
                if file_path in sync_confs:
                    contents = d_man_conf.get("contents")
                    file_path_infos[file_path] = contents

        if not file_path_infos:
            code_num = PARAM_ERROR
            code_string = "No config needs to be synchronized"
            return self.response(code=code_num, message=code_string)
        code_num, code_string, sync_res = Format.deal_batch_sync_res(conf_tools, exist_host, file_path_infos,
                                                                     access_token)

        if code_num != 200:
            return self.response(code=SERVER_ERROR, message=code_string, data=sync_res)
        return self.response(code=SUCCEED, message=code_string, data=sync_res)
