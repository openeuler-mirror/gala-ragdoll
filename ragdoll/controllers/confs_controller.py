import json

import connexion
import os

from ragdoll.const.conf_handler_const import DIRECTORY_FILE_PATH_LIST, NOT_SYNCHRONIZE
from ragdoll.log.log import LOGGER
from ragdoll.models.base_response import BaseResponse  # noqa: E501
from ragdoll.models.batch_sync_req import BatchSyncReq
from ragdoll.models.compare_conf_diff import CompareConfDiff
from ragdoll.models.conf_host import ConfHost  # noqa: E501
from ragdoll.models.domain_ip import DomainIp
from ragdoll.models.domain_name import DomainName  # noqa: E501
from ragdoll.models.domain_names import DomainNames
from ragdoll.models.excepted_conf_info import ExceptedConfInfo  # noqa: E501
from ragdoll.models.sync_req import SyncReq
from ragdoll.models.sync_status import SyncStatus  # noqa: E501
from ragdoll.models.conf_base_info import ConfBaseInfo
from ragdoll.models.conf_is_synced import ConfIsSynced

from ragdoll.controllers.format import Format
from ragdoll.utils.git_tools import GitTools
from ragdoll.utils.yang_module import YangModule
from ragdoll.utils.conf_tools import ConfTools
from ragdoll.utils.host_tools import HostTools
from ragdoll.utils.object_parse import ObjectParse
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
        # body = DomainName.from_dict(connexion.request.get_json())  # noqa: E501
        body = DomainIp.from_dict(connexion.request.get_json())

    domain = body.domain_name
    ip = body.ip
    # check domain
    code_num = 200
    base_rsp = None
    base_rsp, code_num = Format.check_domain_param(domain)
    if code_num != 200:
        return base_rsp, code_num

    # get manage confs in domain
    base_rsp, code_num, manage_confs = Format.get_domain_conf(domain)
    if code_num != 200:
        return base_rsp, code_num
    LOGGER.info("manage_confs is {}".format(manage_confs))
    # get real conf in host
    host_id = Format.get_host_id_by_ip(ip, domain)
    real_conf_res_text = Format.get_realconf_by_domain_and_host(domain, [host_id])
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


def query_excepted_confs(body=None):  # noqa: E501
    """
    query the supported configurations in the current project
    queryExpectedConfs # noqa: E501

    :rtype: List[ExceptedConfInfo]
    """
    # 直接从入参中读取domain列表
    if connexion.request.is_json:
        body = DomainNames.from_dict(connexion.request.get_json())  # noqa: E501
    domain_names = body.domain_names

    if len(domain_names) == 0:
        code_num = 400
        base_rsp = BaseResponse(code_num, "The current domain does not exist, please create the domain first.")
        return base_rsp, code_num

    all_domain_expected_files = []
    yang_modules = YangModule()
    for d_domain in domain_names:
        domain_path = os.path.join(TARGETDIR, d_domain.domain_name)
        expected_conf_lists = ExceptedConfInfo(domain_name=d_domain.domain_name,
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

                    conf_base_info = ConfBaseInfo(file_path=file_path,
                                                  expected_contents=expected_value)
                    expected_conf_lists.conf_base_infos.append(conf_base_info)
        all_domain_expected_files.append(expected_conf_lists)

    LOGGER.debug("all_domain_expected_files is : {}".format(all_domain_expected_files))

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

    object_parse = ObjectParse()
    sync_res = Format.deal_batch_sync_res(conf_tools, exist_host, file_path_infos, object_parse)

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


def compare_conf_diff(body=None):
    """
    compare conf different, return host sync status

    :param body:
    :type body: dict

    :rtype:
    """
    if connexion.request.is_json:
        body = CompareConfDiff.from_dict(connexion.request.get_json())  # noqa: E501
    expected_confs_resp_list = body.expected_confs_resp
    domain_result = body.domain_result
    # 处理expected_confs_resp，将其处理成[{"file_path": "xxx", "contents": "xxx"}], 每个domain都有一个manage_confs
    expected_confs_resp_dict = {}
    for expected_confs_resp in expected_confs_resp_list:
        manage_confs = []
        domain_name = expected_confs_resp.domain_name
        confBaseInfos = expected_confs_resp.conf_base_infos
        for singleConfBaseInfo in confBaseInfos:
            file_path = singleConfBaseInfo.file_path
            contents = singleConfBaseInfo.expected_contents
            single_manage_conf = {"file_path": file_path, "contents": contents}
            manage_confs.append(single_manage_conf)
        expected_confs_resp_dict[domain_name] = manage_confs

    # 处理domain_result,将其处理成[{"domain_name": "aops","host_id": 7, "conf_base_infos": [{"conf_contens": "xxx", "file_path": "xxx"}]}]
    real_conf_res_text_dict = {}
    parse = ObjectParse()
    for domain, host_infos in domain_result.items():
        real_conf_res_text_list = []
        for host_id, confs in host_infos.items():
            signal_host_infos = {"domain_name": domain, "host_id": int(host_id), "conf_base_infos": []}
            for conf in confs:
                conf_path = conf["filePath"]
                conf_info = conf["contents"]
                conf_type = parse.get_conf_type_by_conf_path(conf_path)
                if not conf_type:
                    return
                # create conf model
                conf_model = parse.create_conf_model_by_type(conf_type)
                # 转换解析
                if conf_path not in DIRECTORY_FILE_PATH_LIST:
                    Format.convert_real_conf(conf_model, conf_type, conf_info, conf_path, parse)
                else:
                    pam_res_infos = []
                    for path, content in json.loads(conf_info).items():
                        signal_res_info = {"path": path, "content": content}
                        pam_res_infos.append(signal_res_info)
                    Format.convert_real_conf(conf_model, conf_type, pam_res_infos, conf_path, parse)
                signal_conf = {"file_path": conf["filePath"], "conf_contens": conf_model.conf}
                signal_host_infos["conf_base_infos"].append(signal_conf)
            real_conf_res_text_list.append(signal_host_infos)
        real_conf_res_text_dict[domain] = real_conf_res_text_list

    # 循环real_conf_res_text_list 取出每一个domain的domain_result与expected_confs_resp_dict的expected_confs_resp做对比
    sync_result = []
    for domain_name, real_conf_res_text_list in real_conf_res_text_dict.items():
        expected_confs_resp = expected_confs_resp_dict.get(domain_name)
        sync_status = Format.diff_mangeconf_with_realconf_for_db(domain_name, real_conf_res_text_list,
                                                                 expected_confs_resp)
        domain_name = sync_status.domain_name
        host_status_list = sync_status.host_status

        for signal_status in host_status_list:
            host_id = signal_status.host_id
            domain_host_sync_status = 1
            sync_status_list = signal_status.sync_status
            for single_sync_status in sync_status_list:
                if single_sync_status.is_synced == NOT_SYNCHRONIZE:
                    domain_host_sync_status = 0
                    break
            single_domain_host_status = {"domain_name": domain_name, "host_id": host_id,
                                         "sync_status": domain_host_sync_status}
            sync_result.append(single_domain_host_status)
    return sync_result


def batch_sync_conf_to_host_from_domain(body=None):  # noqa: E501
    """
    synchronize the configuration information of the configuration domain to the host # noqa: E501

    :param body:
    :type body: dict | bytes

    :rtype: List[HostSyncResult]
    """
    if connexion.request.is_json:
        body = BatchSyncReq.from_dict(connexion.request.get_json())  # noqa: E501

    domain = body.domain_name
    host_ids = body.host_ids
    # check domain
    base_rsp, code_num = Format.check_domain_param(domain)
    if code_num != 200:
        return base_rsp, code_num

    # 根据domain和ip获取有哪些不同步的文件
    # get manage confs in domain
    base_rsp, code_num, manage_confs = Format.get_domain_conf(domain)
    if code_num != 200:
        return base_rsp, code_num
    # get real conf in host
    real_conf_res_text = Format.get_realconf_by_domain_and_host(domain, host_ids)
    # compare manage conf with real conf
    sync_status = Format.diff_mangeconf_with_realconf(domain, real_conf_res_text, manage_confs)
    # 解析sync_status，取出未同步的数据
    host_sync_confs = dict()
    host_status = sync_status.host_status
    for host_result in host_status:
        host_id = host_result.host_id
        sync_status = host_result.sync_status
        sync_configs = []
        for sync_result in sync_status:
            if sync_result.is_synced == NOT_SYNCHRONIZE:
                sync_configs.append(sync_result.file_path)
        host_sync_confs[host_id] = sync_configs

    # for sync in sync_status.items():
    #     host_sync_confs[sync.host_id] = sync.sync_configs

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
        code_num = 400
        base_rsp = BaseResponse(400, "No config needs to be synchronized")
        return base_rsp, code_num
    object_parse = ObjectParse()
    sync_res = Format.deal_batch_sync_res(conf_tools, exist_host, file_path_infos, object_parse)

    return sync_res
