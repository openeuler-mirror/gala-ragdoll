import connexion
import six
import os
import requests
from flask import json
from io import StringIO

from ragdoll.log.log import LOGGER
from ragdoll.models.base_response import BaseResponse  # noqa: E501
from ragdoll.models.conf_host import ConfHost  # noqa: E501
from ragdoll.models.domain_name import DomainName  # noqa: E501
from ragdoll.models.excepted_conf_info import ExceptedConfInfo  # noqa: E501
from ragdoll.models.expected_conf import ExpectedConf  # noqa: E501
from ragdoll.models.real_conf_info import RealConfInfo  # noqa: E501
from ragdoll.models.sync_req import SyncReq
from ragdoll.models.sync_status import SyncStatus  # noqa: E501
from ragdoll.models.conf_base_info import ConfBaseInfo
from ragdoll.models.conf_is_synced import ConfIsSynced
from ragdoll.models.conf_synced_res import ConfSyncedRes
from ragdoll.models.realconf_base_info import RealconfBaseInfo
from ragdoll.models.host_sync_result import HostSyncResult
from ragdoll.models.host_sync_status import HostSyncStatus

from ragdoll.models.real_conf import RealConf
from ragdoll.controllers.format import Format
from ragdoll.utils.git_tools import GitTools
from ragdoll.utils.yang_module import YangModule
from ragdoll.utils.conf_tools import ConfTools
from ragdoll.utils.host_tools import HostTools
from ragdoll.utils.object_parse import ObjectParse
from ragdoll import util
from ragdoll.const.conf_files import yang_conf_list

TARGETDIR = GitTools().target_dir


def get_the_sync_status_of_domain(body=None):  # noqa: E501
    """
    get the status of the domain
    get the status of whether the domain has been synchronized # noqa: E501

    :param body:
    :type body: dict | bytes

    :rtype: SyncStatus
    """

    if connexion.request.is_json:
        body = DomainName.from_dict(connexion.request.get_json())  # noqa: E501

    domain = body.domain_name
    # check domain
    code_num = 200
    base_rsp = None
    base_rsp, code_num = Format.check_domain_param(domain)
    if code_num != 200:
        return base_rsp, code_num

    # get manage confs in domain
    LOGGER.debug("############## get the confs in domain ##############")
    base_rsp, code_num, manage_confs = Format._get_domain_conf(domain)
    if code_num != 200:
        return base_rsp, code_num

    # get real conf in host
    LOGGER.debug("############## query the real conf ##############")
    host_ids = Format.get_hostid_list_by_domain(domain)
    real_conf_res_text = Format.get_realconf_by_domain_and_host(domain, host_ids)

    # compare manage conf with real conf 
    sync_status = Format.diff_mangeconf_with_realconf(domain, real_conf_res_text, manage_confs)

    # deal with not found files
    man_conf_list = []
    for d_man_conf in manage_confs:
        man_conf_list.append(d_man_conf.get("file_path").split(":")[-1])
    for d_host in sync_status.host_status:
        d_sync_status = d_host.sync_status
        file_list = []
        for d_file in d_sync_status:
            file_path = d_file.file_path
            file_list.append(file_path)
        for d_man_conf in man_conf_list:
            if d_man_conf in file_list:
                continue
            else:
                comp_res = "NOT FOUND"
                conf_is_synced = ConfIsSynced(file_path=d_man_conf,
                                              is_synced=comp_res)
                d_sync_status.append(conf_is_synced)

    return sync_status


def query_excepted_confs():  # noqa: E501
    """
    query the supported configurations in the current project
    queryExpectedConfs # noqa: E501

    :rtype: List[ExceptedConfInfo]
    """
    # get all domain
    LOGGER.debug("############## get all domain ##############")
    cmd = "ls {}".format(TARGETDIR)
    git_tools = GitTools()
    res_domain = git_tools.run_shell_return_output(cmd).decode().split()

    if len(res_domain) == 0:
        code_num = 400
        base_rsp = BaseResponse(code_num, "The current domain does not exist, please create the domain first.")
        return base_rsp, code_num

    success_domain = []
    all_domain_expected_files = []
    yang_modules = YangModule()
    for d_domian in res_domain:
        domain_path = os.path.join(TARGETDIR, d_domian)
        expected_conf_lists = ExceptedConfInfo(domain_name=d_domian,
                                               conf_base_infos=[])
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

                    git_tools = GitTools()
                    git_message = git_tools.getLogMessageByPath(d_file_path)

                    conf_base_info = ConfBaseInfo(file_path=file_path,
                                                  expected_contents=expected_value,
                                                  change_log=git_message)
                    expected_conf_lists.conf_base_infos.append(conf_base_info)
        all_domain_expected_files.append(expected_conf_lists)

    LOGGER.debug("########################## expetedConfInfo ####################")
    LOGGER.debug("all_domain_expected_files is : {}".format(all_domain_expected_files))
    LOGGER.debug("########################## expetedConfInfo  end ####################")

    if len(all_domain_expected_files) == 0:
        code_num = 400
        base_rsp = BaseResponse(code_num, "The current domain does not exist, please create the domain first.")
        return base_rsp, code_num

    return all_domain_expected_files


def query_real_confs(body=None):  # noqa: E501
    """
    query the real configuration value in the current hostId node

    query the real configuration value in the current hostId node # noqa: E501

    :param body:
    :type body: dict | bytes

    :rtype: List[RealConfInfo]
    """
    if connexion.request.is_json:
        body = ConfHost.from_dict(connexion.request.get_json())  # noqa: E501

    domain = body.domain_name
    host_list = body.host_ids

    check_res = Format.domainCheck(domain)
    if not check_res:
        num = 400
        base_rsp = BaseResponse(num, "Failed to verify the input parameter, please check the input parameters.")
        return base_rsp, num

    # check the domain is Exist
    is_exist = Format.isDomainExist(domain)
    if not is_exist:
        code_num = 400
        base_rsp = BaseResponse(code_num, "The current domain does not exist, please create the domain first.")
        return base_rsp, code_num

    # check whether the host is configured in the domain
    is_host_list_exist = Format.isHostInDomain(domain)
    LOGGER.debug("is_host_list_exist is : {}".format(is_host_list_exist))
    if not is_host_list_exist:
        code_num = 400
        base_rsp = BaseResponse(code_num, "The host information is not set in the current domain." +
                                "Please add the host information first")
        return base_rsp, code_num

    # get all hosts managed by the current domain.
    # If host_list is empty, query all hosts in the current domain.
    # If host_list is not empty, the actual contents of the currently given host are queried.
    exist_host = []
    failed_host = []
    if len(host_list) > 0:
        host_tool = HostTools()
        exist_host, failed_host = host_tool.getHostExistStatus(domain, host_list)
    else:
        LOGGER.debug("############## get the host in domain ##############")
        res_text = Format.get_hostinfo_by_domain(domain)
        if len(res_text) == 0:
            code_num = 404
            base_rsp = BaseResponse(code_num, "The host currently controlled in the domain is empty." +
                                "Please add host information to the domain.")

    if len(exist_host) == 0 or len(failed_host) == len(host_list):
        code_num = 400
        base_rsp = BaseResponse(code_num, "The host information is not set in the current domain." +
                                "Please add the host information first")
        return base_rsp, code_num

    # get the management conf in domain
    LOGGER.debug("############## get the management conf in domain ##############")
    res = Format.get_realconf_by_domain_and_host(domain, exist_host)
    if len(res) == 0:
        code_num = 400
        res_text = "The real configuration does not found."
        base_rsp = BaseResponse(code_num, "Real configuration query failed." +
                                "The failure reason is : " + res_text)
        return base_rsp, code_num

    return res


def sync_conf_to_host_from_domain(body=None):  # noqa: E501
    """
    synchronize the configuration information of the configuration domain to the host # noqa: E501

    :param body:
    :type body: dict | bytes

    :rtype: List[HostSyncResult]
    """
    if connexion.request.is_json:
        body = SyncReq.from_dict(connexion.request.get_json())  # noqa: E501

    domain = body.domain_name
    sync_list = body.sync_list

    host_sync_confs = dict()

    for sync in sync_list:
        host_sync_confs[sync.host_id] = sync.sync_configs

    # check the input domain
    check_res = Format.domainCheck(domain)
    if not check_res:
        num = 400
        base_rsp = BaseResponse(num, "Failed to verify the input parameter, please check the input parameters.")
        return base_rsp, num

    #  check whether the domain exists
    is_exist = Format.isDomainExist(domain)
    if not is_exist:
        code_num = 404
        base_rsp = BaseResponse(code_num, "The current domain does not exist, please create the domain first.")
        return base_rsp, code_num

    # get the management host in domain
    res_host_text = Format.get_hostinfo_by_domain(domain) 
    if len(res_host_text) == 0:
        code_num = 404
        base_rsp = BaseResponse(code_num, "The host currently controlled in the domain is empty." +
                            "Please add host information to the domain.")
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
        code_num = 400
        base_rsp = BaseResponse(code_num, "The host information is not set in the current domain." +
                                "Please add the host information first")
        return base_rsp, code_num

    # get the management conf in domain
    LOGGER.debug("############## get management conf in domain ##############")
    man_conf_res_text = Format.get_manageconf_by_domain(domain)
    LOGGER.debug("man_conf_res_text is : {}".format(man_conf_res_text))
    manage_confs = man_conf_res_text.get("conf_files")
    LOGGER.debug("manage_confs is : {}".format(manage_confs))

    # Deserialize and reverse parse the expected configuration
    conf_tools = ConfTools()
    sync_res = []
    for host_id in exist_host:
        host_sync_result = HostSyncResult(host_id=host_id,
                                          sync_result=[])
        sync_confs = host_sync_confs.get(host_id)
        for d_man_conf in manage_confs:
            file_path = d_man_conf.get("file_path").split(":")[-1]
            if file_path in sync_confs:
                file_path = d_man_conf.get("file_path").split(":")[-1]
                contents = d_man_conf.get("contents")
                object_parse = ObjectParse()
                content = object_parse.parse_json_to_conf(file_path, contents)
                # Configuration to the host
                sync_conf_url = conf_tools.load_url_by_conf().get("sync_url")
                headers = {"Content-Type": "application/json"}
                data = {"host_id": host_id, "file_path": file_path, "content": content}
                sync_response = requests.put(sync_conf_url, data=json.dumps(data), headers=headers)

                resp_code = json.loads(sync_response.text).get('code')
                resp = json.loads(sync_response.text).get('data').get('resp')
                conf_sync_res = ConfSyncedRes(file_path=file_path,
                                              result="")
                if resp_code == "200" and resp.get('sync_result') is True:
                    conf_sync_res.result = "SUCCESS"
                else:
                    conf_sync_res.result = "FAILED"
                host_sync_result.sync_result.append(conf_sync_res)
        sync_res.append(host_sync_result)

    return sync_res


def query_supported_confs(body=None):
    """
        query supported configuration list # noqa: E501

       :param body:
       :type body: dict | bytes

       :rtype: List
    """
    if connexion.request.is_json:
        body = DomainName.from_dict(connexion.request.get_json())

    domain = body.domain_name

    check_res = Format.domainCheck(domain)
    if not check_res:
        code_num = 400
        base_rsp = BaseResponse(code_num, "Failed to verify the input parameter, please check the input parameters.")
        return base_rsp, code_num

    is_exist = Format.isDomainExist(domain)
    if not is_exist:
        code_num = 404
        base_rsp = BaseResponse(code_num, "The current domain does not exist, please create the domain first.")
        return base_rsp, code_num

    conf_files = Format.get_manageconf_by_domain(domain)
    conf_files = conf_files.get("conf_files")
    if len(conf_files) == 0:
        return yang_conf_list

    exist_conf_list = []
    for conf in conf_files:
        exist_conf_list.append(conf.get('file_path'))

    return list(set(yang_conf_list).difference(set(exist_conf_list)))
