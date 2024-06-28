import glob
import os
import queue
import re
import json
import ast
import subprocess
import threading
import time
from typing import List, Dict
from urllib.parse import urlencode

import requests
import yaml
from flask import g

from vulcanus.conf.constant import HOSTS_FILTER
from vulcanus.restful.resp.state import SUCCEED

from ragdoll.app import configuration
from vulcanus.log.log import LOGGER

from ragdoll.app.constant import NOT_SYNCHRONIZE, SYNCHRONIZED, DIRECTORY_FILE_PATH_LIST, HOST_PATH_FILE, \
    KEY_FILE_PREFIX, KEY_FILE_SUFFIX, PARENT_DIRECTORY, SYNC_LOG_PATH, SYNC_CONFIG_YML
from ragdoll.app.models.base_response import BaseResponse  # noqa: E501
from ragdoll.app.models.conf_file import ConfFile
from ragdoll.app.models.conf_files import ConfFiles
from ragdoll.app.models.host import Host  # noqa: E501
from ragdoll.app.utils.host_tools import HostTools


class Format(object):

    @staticmethod
    def domainCheck(domainName):
        res = True
        if not re.match(r"^[A-Za-z0-9_\.-]*$", domainName) or domainName == "" or len(domainName) > 255:
            res = False
        return res

    @staticmethod
    def isDomainExist(domainName):
        from ragdoll.app import TARGETDIR
        domainPath = os.path.join(TARGETDIR, domainName)
        if os.path.exists(domainPath):
            return True

        return False

    @staticmethod
    def spliceAllSuccString(obj, operation, succDomain):
        """
        docstring
        """
        codeString = "All {obj} {oper} successfully, {succ} {obj} in total.".format(obj=obj, oper=operation,
                                                                                    succ=len(succDomain))
        return codeString

    @staticmethod
    def splicErrorString(obj, operation, succDomain, failDomain):
        """
        docstring
        """
        codeString = "{succ} {obj} {oper} successfully, {fail} {obj} {oper} failed.".format( \
            succ=len(succDomain), obj=obj, oper=operation, fail=len(failDomain))

        succString = "\n"
        if len(succDomain) > 0:
            succString = "These are successful: "
            for succName in succDomain:
                succString += succName + " "
            succString += "."

        if len(failDomain) > 0:
            failString = "These are failed: "
            for failName in failDomain:
                failString += failName + " "
            return codeString + succString + failString

        return codeString + succString

    @staticmethod
    def two_abs_join(abs1, abs2):
        """
        Absolute path Joins two absolute paths together
        :param abs1:  main path
        :param abs2:  the spliced path
        :return: together the path
        """
        # 1. Format path (change \\ in path to \)
        abs2 = os.fspath(abs2)

        # 2. Split the path file
        abs2 = os.path.splitdrive(abs2)[1]
        # 3. Remove the beginning '/'
        abs2 = abs2.strip('\\/') or abs2
        return os.path.abspath(os.path.join(abs1, abs2))

    @staticmethod
    def isContainedHostIdInfile(f_file, content):
        isContained = False
        with open(f_file, 'r') as d_file:
            for line in d_file.readlines():
                line_dict = json.loads(str(ast.literal_eval(line)).replace("'", "\""))
                if content == line_dict["host_id"]:
                    isContained = True
                    break
        return isContained

    @staticmethod
    def isContainedHostIdInOtherDomain(content):
        from ragdoll.app import TARGETDIR
        isContained = False
        contents = os.listdir(TARGETDIR)
        folders = [f for f in contents if os.path.isdir(os.path.join(TARGETDIR, f))]
        for folder in folders:
            hostPath = os.path.join(os.path.join(TARGETDIR, folder), "hostRecord.txt")
            if os.path.isfile(hostPath):
                with open(hostPath, 'r') as d_file:
                    for line in d_file.readlines():
                        line_dict = json.loads(str(ast.literal_eval(line)).replace("'", "\""))
                        if content == line_dict["host_id"]:
                            isContained = True
                            break
        return isContained

    @staticmethod
    def addHostToFile(d_file, host):
        host = {'host_id': host["hostId"], 'ip': host["ip"], 'ipv6': host["ipv6"]}
        info_json = json.dumps(str(host), sort_keys=False, indent=4, separators=(',', ': '))
        os.umask(0o077)
        with open(d_file, 'a+') as host_file:
            host_file.write(info_json)
            host_file.write("\n")

    @staticmethod
    def getSubDirFiles(path):
        """
        desc: Subdirectory records and files need to be logged to the successConf
        """
        fileRealPathList = []
        fileXPathlist = []
        for root, dirs, files in os.walk(path):
            if len(files) > 0:
                preXpath = root.split('/', 3)[3]
                for d_file in files:
                    xpath = os.path.join(preXpath, d_file)
                    fileXPathlist.append(xpath)
                    realPath = os.path.join(root, d_file)
                    fileRealPathList.append(realPath)

        return fileRealPathList, fileXPathlist

    @staticmethod
    def isHostInDomain(domainName):
        """
        desc: Query domain Whether host information is configured in the domain
        """
        from ragdoll.app import TARGETDIR
        isHostInDomain = False
        domainPath = os.path.join(TARGETDIR, domainName)
        hostPath = os.path.join(domainPath, "hostRecord.txt")
        if os.path.isfile(hostPath):
            isHostInDomain = True

        return isHostInDomain

    @staticmethod
    def isHostIdExist(hostPath, hostId):
        """
        desc: Query hostId exists within the current host domain management
        """
        isHostIdExist = False
        if os.path.isfile(hostPath) and os.stat(hostPath).st_size > 0:
            with open(hostPath) as h_file:
                for line in h_file.readlines():
                    if hostId in line:
                        isHostIdExist = True
                        break

        return isHostIdExist

    @staticmethod
    def get_file_content_by_readlines(d_file):
        """
        desc: remove empty lines and comments from d_file
        """
        res = []
        try:
            with open(d_file, 'r') as s_f:
                lines = s_f.readlines()
                for line in lines:
                    tmp = line.strip()
                    if not len(tmp) or tmp.startswith("#"):
                        continue
                    res.append(line)
        except FileNotFoundError:
            LOGGER.error(f"File not found: {d_file}")
        except IOError as e:
            LOGGER.error(f"IO error: {e}")
        except Exception as e:
            LOGGER.error(f"An error occurred: {e}")
        return res

    @staticmethod
    def get_file_content_by_read(d_file):
        """
        desc: return a string after read the d_file
        """
        if not os.path.exists(d_file):
            return ""
        with open(d_file, 'r') as s_f:
            lines = s_f.read()
        return lines

    @staticmethod
    def rsplit(_str, seps):
        """
        Splits _str by the first sep in seps that is found from the right side.
        Returns a tuple without the separator.
        """
        for idx, ch in enumerate(reversed(_str)):
            if ch in seps:
                return _str[0:-idx - 1], _str[-idx:]

    @staticmethod
    def arch_sep(package_string):
        """
        Helper method for finding if arch separator is '.' or '-'

        Args:
            package_string (str): dash separated package string such as 'bash-4.2.39-3.el7'.

        Returns:
            str: arch separator
        """
        return '.' if package_string.rfind('.') > package_string.rfind('-') else '-'

    @staticmethod
    def set_file_content_by_path(content, path):
        res = 0
        if os.path.exists(path):
            with open(path, 'w+') as d_file:
                for d_cont in content:
                    d_file.write(d_cont)
                    d_file.write("\n")
            res = 1
        return res

    @staticmethod
    def get_git_dir():
        return configuration.git.git_dir

    @staticmethod
    def get_hostinfo_by_domain(domainName):
        """
        desc: Query hostinfo by domainname
        """
        from ragdoll.app import TARGETDIR
        LOGGER.debug("Get hostinfo by domain : {}".format(domainName))
        hostlist = []
        domainPath = os.path.join(TARGETDIR, domainName)
        hostPath = os.path.join(domainPath, "hostRecord.txt")
        if not os.path.isfile(hostPath) or os.stat(hostPath).st_size == 0:
            return hostlist
        try:
            with open(hostPath, 'r') as d_file:
                for line in d_file.readlines():
                    json_str = json.loads(line)
                    host_json = ast.literal_eval(json_str)
                    hostId = host_json["host_id"]
                    ip = host_json["ip"]
                    ipv6 = host_json["ipv6"]
                    host = Host(host_id=hostId, ip=ip, ipv6=ipv6)
                    hostlist.append(host.to_dict())
        except OSError as err:
            LOGGER.error("OS error: {0}".format(err))
            return hostlist
        if len(hostlist) == 0:
            LOGGER.debug("Hostlist is empty !")
        else:
            LOGGER.debug("Hostlist is : {}".format(hostlist))
        return hostlist

    @staticmethod
    def get_host_id_by_ip(ip, domainName):
        """
        desc: Query hostinfo by host ip
        """
        from ragdoll.app import TARGETDIR
        LOGGER.debug("Get hostinfo by ip : {}".format(ip))
        hostlist = []
        domainPath = os.path.join(TARGETDIR, domainName)
        hostPath = os.path.join(domainPath, "hostRecord.txt")
        if not os.path.isfile(hostPath) or os.stat(hostPath).st_size == 0:
            return hostlist
        try:
            with open(hostPath, 'r') as d_file:
                for line in d_file.readlines():
                    json_str = json.loads(line)
                    host_json = ast.literal_eval(json_str)
                    if host_json["ip"] == ip:
                        return host_json["host_id"]
        except OSError as err:
            LOGGER.error("OS error: {0}".format(err))

    @staticmethod
    def get_manageconf_by_domain(domain):
        from ragdoll.app import TARGETDIR
        LOGGER.debug("Get manageconf by domain : {}".format(domain))
        expected_conf_lists = ConfFiles(domain_name=domain, conf_files=[])
        domainPath = os.path.join(TARGETDIR, domain)
        from ragdoll.app.utils.yang_module import YangModule
        for root, dirs, files in os.walk(domainPath):
            if len(files) > 0 and len(root.split('/')) > 3:
                if "hostRecord.txt" in files:
                    continue
                for d_file in files:
                    d_file_path = os.path.join(root, d_file)
                    contents = Format.get_file_content_by_read(d_file_path)
                    feature = os.path.join(root.split('/')[-1], d_file)
                    yang_modules = YangModule()
                    d_module = yang_modules.getModuleByFeature(feature)
                    file_lists = yang_modules.getFilePathInModdule(yang_modules.module_list)
                    file_path = file_lists.get(d_module.name()).split(":")[-1]

                    conf = ConfFile(file_path=file_path, contents=contents)
                    expected_conf_lists.conf_files.append(conf)

        LOGGER.debug("Expected_conf_lists is :{}".format(expected_conf_lists))
        return expected_conf_lists.to_dict()

    @staticmethod
    def get_realconf_by_domain_and_host(domain, exist_host):
        res = []
        conf_files = Format.get_manageconf_by_domain(domain)
        # get the real conf in host
        conf_list = []
        from ragdoll.app.utils.object_parse import ObjectParse
        for d_conf in conf_files.get("conf_files"):
            file_path = d_conf.get("file_path").split(":")[-1]
            if file_path not in DIRECTORY_FILE_PATH_LIST:
                conf_list.append(file_path)
            else:
                d_conf_cs = d_conf.get("contents")
                d_conf_contents = json.loads(d_conf_cs)
                for d_conf_key, d_conf_value in d_conf_contents.items():
                    conf_list.append(d_conf_key)
        get_real_conf_body = {}
        get_real_conf_body_info = []
        for d_host in exist_host:
            get_real_conf_body_infos = {}
            get_real_conf_body_infos["host_id"] = d_host
            get_real_conf_body_infos["config_list"] = conf_list
            get_real_conf_body_info.append(get_real_conf_body_infos)
        get_real_conf_body["infos"] = get_real_conf_body_info
        codeNum, codeString, resp = Format.collect_config(get_real_conf_body)
        if codeNum != 200:
            return res

        if not resp or len(resp) == 0:
            return res

        success_lists = {}
        failed_lists = {}

        for d_res in resp:
            d_host_id = d_res.get("host_id")
            fail_files = d_res.get("fail_files")
            if len(fail_files) > 0:
                failed_lists["host_id"] = d_host_id
                failed_lists_conf = []
                for d_failed in fail_files:
                    failed_lists_conf.append(d_failed)
                failed_lists["failed_conf"] = failed_lists_conf
                failed_lists["success_conf"] = []
            else:
                success_lists["host_id"] = d_host_id
                success_lists["success_conf"] = []
                success_lists["failed_conf"] = []

            read_conf_info = {"domainName": domain, "hostID": d_host_id, "confBaseInfos": []}
            d_res_infos = d_res.get("infos")

            real_directory_conf = {}
            real_directory_conf_list = {}
            object_parse = ObjectParse()
            for d_file in d_res_infos:
                content = d_file.get("content")
                file_path = d_file.get("path")
                file_attr = d_file.get("file_attr").get("mode")
                file_owner = "({}, {})".format(d_file.get("file_attr").get("group"),
                                               d_file.get("file_attr").get("owner"))
                directory_flag = False
                for dir_path in DIRECTORY_FILE_PATH_LIST:
                    if str(file_path).find(dir_path) != -1:
                        if real_directory_conf.get(dir_path) is None:
                            real_directory_conf_list[dir_path] = list()
                            real_directory_conf[dir_path] = {"filePath": dir_path, "fileAttr": file_attr,
                                                             "fileOwner": file_owner, "confContents": ""}
                        directory_conf = dict()
                        directory_conf["path"] = file_path
                        directory_conf["content"] = content
                        real_directory_conf_list.get(dir_path).append(directory_conf)
                        directory_flag = True
                        break
                if not directory_flag:
                    Format.deal_conf_list_content(content, d_file, file_path, object_parse, read_conf_info)
                if len(fail_files) > 0:
                    failed_lists.get("success_conf").append(file_path)
                else:
                    success_lists.get("success_conf").append(file_path)

            for dir_path, dir_value in real_directory_conf_list.items():
                content_string = object_parse.parse_directory_single_conf_to_json(dir_value,
                                                                                  real_directory_conf[
                                                                                      dir_path]["filePath"])
                real_directory_conf[dir_path]["confContents"] = content_string
                real_conf_base_info = real_directory_conf.get(dir_path)

                read_conf_info.get("confBaseInfos").append(real_conf_base_info)
            res.append(read_conf_info)
        return res

    @staticmethod
    def deal_conf_list_content(content, d_file, file_path, object_parse, read_conf_info):
        content_string = object_parse.parse_conf_to_json(file_path, content)
        file_attr = d_file.get("file_attr").get("mode")
        file_owner = "({}, {})".format(d_file.get("file_attr").get("group"),
                                       d_file.get("file_attr").get("owner"))
        real_conf_base_info = {"path": file_path, "filePath": file_path, "fileAttr": file_attr, "fileOwner": file_owner,
                               "confContents": content_string}
        read_conf_info.get("confBaseInfos").append(real_conf_base_info)

    @staticmethod
    def check_domain_param(domain):
        code_num = 200
        base_resp = None
        check_res = Format.domainCheck(domain)
        if not check_res:
            num = 400
            base_rsp = BaseResponse(num, "Failed to verify the input parameter, please check the input parameters.")
            return base_rsp, num

        # check the domain is existed
        is_exist = Format.isDomainExist(domain)
        if not is_exist:
            code_num = 404
            base_rsp = BaseResponse(code_num, "The current domain does not exist, please create the domain first.")
            return base_rsp, code_num

        # get the existed result of the host in domain
        is_host_list_exist = Format.isHostInDomain(domain)
        if not is_host_list_exist:
            code_num = 404
            base_resp = BaseResponse(code_num, "The host information is not set in the current domain." +
                                     "Please add the host information first")
        return base_resp, code_num

    @staticmethod
    def get_hostid_list_by_domain(domain):
        host_ids = []
        res_text = Format.get_hostinfo_by_domain(domain)
        if len(res_text) == 0:
            return host_ids

        host_tools = HostTools()
        host_ids = host_tools.getHostList(res_text)
        return host_ids

    @staticmethod
    def get_domain_conf(domain):
        code_num = 200
        base_resp = None
        # get the host info in domain
        LOGGER.debug("Get the conf by domain: {}.".format(domain))
        host_ids = Format.get_hostid_list_by_domain(domain)
        if not host_ids:
            code_num = 404
            base_resp = BaseResponse(code_num, "The host currently controlled in the domain is empty." +
                                     "Please add host information to the domain.")
            return base_resp, code_num, list()

        # get the manage conf in domain
        man_conf_res_text = Format.get_manageconf_by_domain(domain)
        manage_confs = man_conf_res_text.get("conf_files")

        if len(manage_confs) == 0:
            code_num = 404
            base_resp = BaseResponse(code_num, "The configuration is not set in the current domain." +
                                     "Please add the configuration information first.")
            return base_resp, code_num, list()
        return base_resp, code_num, manage_confs

    @staticmethod
    def diff_manageconf_with_realconf(domain, real_conf_res_text, manage_confs):
        sync_status = {"domainName": domain, "hostStatus": []}

        from ragdoll.app.utils.object_parse import ObjectParse

        for d_real_conf in real_conf_res_text:
            host_id = d_real_conf["hostID"]
            host_sync_status = {"hostId": host_id, "syncStatus": []}
            d_real_conf_base = d_real_conf["confBaseInfos"]
            for d_conf in d_real_conf_base:
                directory_conf_is_synced = {"file_path": "", "isSynced": "", "singleConf": []}
                d_conf_path = d_conf["filePath"]

                object_parse = ObjectParse()
                # get the conf type and model
                conf_type, conf_model = Format.get_conf_type_model(d_conf_path, object_parse)

                Format.deal_conf_sync_status(conf_model, d_conf, d_conf_path, directory_conf_is_synced,
                                             host_sync_status, manage_confs)

                if len(directory_conf_is_synced.get("singleConf")) > 0:
                    synced_flag = SYNCHRONIZED
                    for single_config in directory_conf_is_synced.get("singleConf"):
                        if single_config.get("singleIsSynced") == SYNCHRONIZED:
                            continue
                        else:
                            synced_flag = NOT_SYNCHRONIZE
                    directory_conf_is_synced["isSynced"] = synced_flag
                    host_sync_status.get("syncStatus").append(directory_conf_is_synced)
            sync_status.get("hostStatus").append(host_sync_status)
        return sync_status

    @staticmethod
    def deal_conf_sync_status(conf_model, d_conf, d_conf_path, directory_conf_is_synced, host_sync_status,
                              manage_confs):
        comp_res = ""
        if d_conf_path in DIRECTORY_FILE_PATH_LIST:
            confContents = json.loads(d_conf["confContents"])
            directory_conf_contents = ""
            for d_man_conf in manage_confs:
                d_man_conf_path = d_man_conf.get("file_path")
                if d_man_conf_path != d_conf_path:
                    continue
                else:
                    directory_conf_is_synced["file_path"] = d_conf_path
                    directory_conf_contents = d_man_conf.get("contents")

            directory_conf_contents_dict = json.loads(directory_conf_contents)

            for dir_conf_content_key, dir_conf_content_value in directory_conf_contents_dict.items():
                if dir_conf_content_key not in confContents.keys():
                    single_conf = {"singleFilePath": dir_conf_content_key, "singleIsSynced": NOT_SYNCHRONIZE}
                    directory_conf_is_synced.get("singleConf").append(single_conf)
                else:
                    dst_conf = confContents.get(dir_conf_content_key)
                    comp_res = conf_model.conf_compare(dir_conf_content_value, dst_conf)
                    single_conf = {"singleFilePath": dir_conf_content_key, "singleIsSynced": comp_res}
                    directory_conf_is_synced.get("singleConf").append(single_conf)
        else:
            for d_man_conf in manage_confs:
                if d_man_conf.get("file_path").split(":")[-1] != d_conf_path:
                    continue
                comp_res = conf_model.conf_compare(d_man_conf.get("contents"), d_conf["confContents"])
            conf_is_synced = {"file_path": d_conf_path, "isSynced": comp_res}
            host_sync_status.get("syncStatus").append(conf_is_synced)

    @staticmethod
    def convert_real_conf(conf_model, conf_type, conf_info, conf_path, parse):
        # load yang model info
        yang_info = parse._yang_modules.getModuleByFilePath(conf_path)
        conf_model.load_yang_model(yang_info)

        # load conf info
        if conf_type == "kv":
            spacer_type = parse._yang_modules.getSpacerInModdule([yang_info])
            conf_model.read_conf(conf_info, spacer_type, yang_info)
        else:
            conf_model.read_conf(conf_info)

    @staticmethod
    def deal_conf_sync_status_for_db(conf_model, d_conf, d_conf_path, directory_conf_is_synced, host_sync_status,
                                     manage_confs):
        comp_res = ""
        if d_conf_path in DIRECTORY_FILE_PATH_LIST:
            confContents = d_conf.get("conf_contents")
            directory_conf_contents = ""
            for d_man_conf in manage_confs:
                d_man_conf_path = d_man_conf.get("file_path")
                if d_man_conf_path != d_conf_path:
                    continue
                else:
                    directory_conf_is_synced["file_path"] = d_conf_path
                    directory_conf_contents = d_man_conf.get("contents")

            directory_conf_contents_dict = json.loads(directory_conf_contents)

            for dir_conf_content_key, dir_conf_content_value in directory_conf_contents_dict.items():
                if dir_conf_content_key not in confContents.keys():
                    single_conf = {"singleFilePath": dir_conf_content_key, "singleIsSynced": NOT_SYNCHRONIZE}
                    directory_conf_is_synced["singleConf"].append(single_conf)
                else:
                    dst_conf = confContents.get(dir_conf_content_key)
                    comp_res = conf_model.conf_compare(dir_conf_content_value, dst_conf)
                    single_conf = {"singleFilePath": dir_conf_content_key, "singleIsSynced": comp_res}
                    directory_conf_is_synced["singleConf"].append(single_conf)
        else:
            for d_man_conf in manage_confs:
                if d_man_conf.get("file_path").split(":")[-1] != d_conf_path:
                    continue
                contents = d_man_conf.get("contents")
                comp_res = conf_model.conf_compare(contents, json.dumps(d_conf.get("conf_contents")))
            conf_is_synced = {"file_path": d_conf_path, "isSynced": comp_res}
            host_sync_status["syncStatus"].append(conf_is_synced)

    @staticmethod
    def get_conf_type_model(d_conf_path, object_parse):
        for dir_path in DIRECTORY_FILE_PATH_LIST:
            if str(d_conf_path).find(dir_path) != -1:
                conf_type = object_parse.get_conf_type_by_conf_path(dir_path)
                conf_model = object_parse.create_conf_model_by_type(conf_type)
            else:
                conf_type = object_parse.get_conf_type_by_conf_path(d_conf_path)
                conf_model = object_parse.create_conf_model_by_type(conf_type)
            return conf_type, conf_model

    @staticmethod
    def deal_batch_sync_res(exist_host, file_path_infos):
        from ragdoll.app.utils.object_parse import ObjectParse
        object_parse = ObjectParse()
        codeNum = 200
        # 组装参数
        sync_config_request = {"host_ids": exist_host, "file_path_infos": list()}
        for file_path, contents in file_path_infos.items():
            if file_path in DIRECTORY_FILE_PATH_LIST:
                for directory_file_path, directory_content in json.loads(contents).items():
                    content = object_parse.parse_json_to_conf(directory_file_path, directory_content)
                    single_file_path_info = {"file_path": directory_file_path, "content": content}
                    sync_config_request["file_path_infos"].append(single_file_path_info)
            else:
                content = object_parse.parse_json_to_conf(file_path, contents)
                single_file_path_info = {"file_path": file_path, "content": content}
                sync_config_request["file_path_infos"].append(single_file_path_info)
        # 调用zeus接口
        resp_code, codeString, resp = Format.batch_sync_config(sync_config_request)
        if resp_code != 200:
            codeNum = 500
            codeString = f"Failed to sync configuration, reason is {codeString}, please check the interface of " \
                         f"config/sync. "
            return codeNum, codeString, []

        # 重新构建返回值，目录文件返回值重新构造
        sync_res = []
        for host_result in resp:
            syncResult = []
            conf_sync_res_list = []
            sync_result_list = host_result.get("syncResult")
            dir_name = ""
            for single_result in sync_result_list:
                dir_name = os.path.dirname(single_result.get("filePath"))
                if dir_name in DIRECTORY_FILE_PATH_LIST and single_result.get("result") == "SUCCESS":
                    conf_sync_res_list.append("SUCCESS")
                elif dir_name in DIRECTORY_FILE_PATH_LIST and single_result.get("result") == "FAIL":
                    conf_sync_res_list.append("FAILED")
                else:
                    syncResult.append(single_result)
            if conf_sync_res_list:
                if "FAILED" in conf_sync_res_list:
                    directory_sync_result = {"filePath": dir_name, "result": "FAILED"}
                else:
                    directory_sync_result = {"filePath": dir_name, "result": "SUCCESS"}
                syncResult.append(directory_sync_result)
            single_host_sync_result = {"host_id": host_result.get("host_id"), "syncResult": syncResult}
            sync_res.append(single_host_sync_result)
        return codeNum, codeString, sync_res

    @staticmethod
    def addHostSyncStatus(domain, host_infos):
        # 数据入库
        try:
            from ragdoll.app.proxy.host_conf_sync_status import HostConfSyncStatusProxy
            add_host_sync_status_list = list()
            for host in host_infos:
                host_sync_status = {
                    "host_id": host.get("hostId"),
                    "host_ip": host.get("ip"),
                }
                add_host_sync_status_list.append(host_sync_status)
            callback = HostConfSyncStatusProxy()
            callback.connect()
            result = callback.add_host_sync_status(domain, add_host_sync_status_list)
            if result != SUCCEED:
                LOGGER.error(
                    "Failed to add host sync status, please check the interface of /manage/host/sync/status/add.")
        except requests.exceptions.RequestException as connect_ex:
            LOGGER.error(f"An error occurred: {connect_ex}")
            LOGGER.error("Failed to add host sync status, please check the interface of /manage/host/sync/status/add.")

    @staticmethod
    def deleteHostSyncStatus(domain, hostInfos):
        # 数据入库
        try:
            from ragdoll.app.proxy.host_conf_sync_status import HostConfSyncStatusProxy
            delete_host_sync_status_list = []
            for host in hostInfos:
                delete_host_sync_status = {
                    "host_id": host.get("hostId"),
                }
                delete_host_sync_status_list.append(delete_host_sync_status)
            callback = HostConfSyncStatusProxy()
            callback.connect()
            result = callback.delete_host_sync_status(domain, delete_host_sync_status_list)
            if result != SUCCEED:
                LOGGER.error(
                    "Failed to delete host sync status, please check the interface of "
                    "/manage/host/sync/status/delete.")
        except requests.exceptions.RequestException as connect_ex:
            LOGGER.error(f"An error occurred: {connect_ex}")
            LOGGER.error(
                "Failed to delete host sync status, please check the interface of "
                "/manage/host/sync/status/delete.")

    @staticmethod
    def diff_mangeconf_with_realconf_for_db(domain, real_conf_res_text, manage_confs):
        sync_status = {"domainName": domain, "hostStatus": []}
        from ragdoll.app.utils.object_parse import ObjectParse

        for d_real_conf in real_conf_res_text:
            host_id = d_real_conf.get('host_id')
            host_sync_status = {"hostId": host_id, "syncStatus": []}
            d_real_conf_base = d_real_conf.get('conf_base_infos')
            for d_conf in d_real_conf_base:
                directory_conf_is_synced = {"file_path": "", "isSynced": "", "singleConf": []}
                d_conf_path = d_conf.get('file_path')
                object_parse = ObjectParse()
                # get the conf type and model
                conf_type, conf_model = Format.get_conf_type_model(d_conf_path, object_parse)
                Format.deal_conf_sync_status_for_db(conf_model, d_conf, d_conf_path, directory_conf_is_synced,
                                                    host_sync_status, manage_confs)

                if len(directory_conf_is_synced["singleConf"]) > 0:
                    synced_flag = SYNCHRONIZED
                    for single_config in directory_conf_is_synced["singleConf"]:
                        if single_config["singleIsSynced"] == SYNCHRONIZED:
                            continue
                        else:
                            synced_flag = NOT_SYNCHRONIZE
                    directory_conf_is_synced["isSynced"] = synced_flag
                    host_sync_status["syncStatus"].append(directory_conf_is_synced)
            sync_status.get("hostStatus").append(host_sync_status)
        return sync_status

    @staticmethod
    def deal_expected_confs_resp(expected_confs_resp_list):
        """"
            deal the excepted confs resp.

        Args:
            expected_confs_resp_list (list): e.g
                [
                    {
                        "domainName": "xx"
                        "confBaseInfos": [
                            {
                                "filePath": "xx",
                                "expectedContents": "xxx"
                            }
                        ]
                    }
                ]
        Returns:
            dict: e.g
            {
                "aops": [
                    {
                        "file_path": "xxx",
                        "contents": "xxx"
                    }
                ]
            }
        """
        # 处理expected_confs_resp，将其处理成[{"file_path": "xxx", "contents": "xxx"}], 每个domain都有一个manage_confs
        expected_confs_resp_dict = {}
        for expected_confs_resp in expected_confs_resp_list:
            manage_confs = []
            domain_name = expected_confs_resp["domainName"]
            confBaseInfos = expected_confs_resp["confBaseInfos"]
            for singleConfBaseInfo in confBaseInfos:
                file_path = singleConfBaseInfo["filePath"]
                contents = singleConfBaseInfo["expectedContents"]
                single_manage_conf = {"file_path": file_path, "contents": contents}
                manage_confs.append(single_manage_conf)
            expected_confs_resp_dict[domain_name] = manage_confs
        return expected_confs_resp_dict

    @staticmethod
    def deal_domain_result(domain_result):
        """"
            deal the domain result.

        Args:
            domain_result (object): e.g
                {
                    "aops": {
                        "1": [
                            {
                                "filePath": "xxx",
                                "contents": "xxxx"
                            }
                        ]
                    }
                }
        Returns:
            dict: e.g
            {
                "aops": [
                    {
                        "domain_name": "xxx",
                        "host_id": 1,
                        "conf_base_infos": [
                            {
                                "file_path": "xxx",
                                "conf_contents": {} or []
                            }
                        ]
                    }
                ]
            }
        """
        # 处理domain_result,将其处理成[{"domain_name": "aops","host_id": 7, "conf_base_infos": [{"conf_contents": "xxx", "file_path": "xxx"}]}]
        from ragdoll.app.utils.object_parse import ObjectParse
        real_conf_res_text_dict = {}
        parse = ObjectParse()
        for domain, host_infos in domain_result.items():
            real_conf_res_text_list = []
            for host_id, confs in host_infos.items():
                signal_host_infos = {"domain_name": domain, "host_id": host_id, "conf_base_infos": []}
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
                    signal_conf = {"file_path": conf["filePath"], "conf_contents": conf_model.conf}
                    signal_host_infos["conf_base_infos"].append(signal_conf)
                real_conf_res_text_list.append(signal_host_infos)
            real_conf_res_text_dict[domain] = real_conf_res_text_list
        return real_conf_res_text_dict

    @staticmethod
    def is_not_in_clusters(request_clusters, allowed_clusters):
        for item in request_clusters:
            if item not in allowed_clusters:
                return True
        return False

    @staticmethod
    def convert_host_id_to_failed_data_format(host_id_list: list, host_id_with_file: dict) -> list:
        """
        convert host id which can't visit to target data format

        Args:
            host_id_list (list)
            host_id_with_file: host id and all requested file path. e.g
                {
                    host_id_1: [config_path_1, config_path_2, ...],
                    host_id_2: [config_path_1, config_path_2, ...]
                }

        Returns:
            List[Dict]:  e.g
                [{
                    host_id: host_id,
                    success_files: [],
                    fail_files: [all file path],
                    infos: []
               }]
        """
        return [
            {'host_id': host_id, 'success_files': [], 'fail_files': host_id_with_file.get(host_id), 'infos': []}
            for host_id in host_id_list
        ]

    @staticmethod
    def generate_target_data_format(collect_result_list: List[Dict], host_id_with_file: Dict[str, List]) -> List:
        """
        Generate target data format


        Args:
            collect_result_list: file content list
            host_id_with_file:  host id and all requested file path

        Returns:
            target data format: e.g
                [
                    {
                        host_id: host_id,
                        infos: [
                            path: file_path,
                            content: string,
                            file_attr: {
                                owner: root,
                                mode: 0644,
                                group: root
                            }
                        ],
                        success_files:[ file_path ],
                        fail_files:[ file_path ]
                    }
                ]
        """
        file_content = []
        valid_host_id = set()
        for collect_result in collect_result_list:
            if collect_result.get('infos') is not None:
                file_content.append(collect_result)
                valid_host_id.add(collect_result.get('host_id'))

        invalid_host_id = set(host_id_with_file.keys()) - valid_host_id
        read_failed_data = Format.convert_host_id_to_failed_data_format(list(invalid_host_id), host_id_with_file)
        file_content.extend(read_failed_data)

        return file_content

    @staticmethod
    def get_file_content(host_info: Dict, file_list: list) -> Dict:
        """
            Get target file content from ceres.

        Args:
            host_info (dict): e.g
                {
                    host_id : xx,
                    address : xx,
                    header  : xx
                }
            file_list (list): e.g
                ["/etc/test.txt", "/tmp/test.csv"]
        Returns:
            dict: e.g
            {
                'fail_files': [],
                'infos': [{
                    'content': 'string',
                    'file_attr': {
                    'group': 'root',
                    'mode': '0644',
                    'owner': 'root'},
                    'path': 'file_path'
                    }],
                'success_files': ['file_path'],
                'host_id': 'host_id'
            }

        """
        from vulcanus.conf.constant import CERES_COLLECT_FILE
        from ragdoll.app.core.ssh import execute_command_and_parse_its_result
        from ragdoll.app.core.model import ClientConnectArgs
        command = CERES_COLLECT_FILE % json.dumps(file_list)
        status, content = execute_command_and_parse_its_result(
            ClientConnectArgs(
                host_info.get("host_ip"), host_info.get("ssh_port"), host_info.get("ssh_user"), host_info.get("pkey")
            ),
            command,
        )
        if status == SUCCEED:
            data = json.loads(content)
            data.update({"host_id": host_info["host_id"]})
            return data
        return {"host_id": host_info["host_id"], "config_file_list": file_list}

    @staticmethod
    def collect_config(real_conf_body: dict):
        """
            Get config
            Args:
                real_conf_body: {
                    "infos": [{
                        "host_id": "f",
                        "config_list": ["/xx", "/exxxo"]
                    }]
                }
            Returns:
                dict: e.g
                resp:[
                        {
                            host_id: host_id,
                            infos: [
                                path: file_path1,
                                content: string,
                                file_attr: {
                                    owner: root,
                                    mode: 0644,
                                    group: root
                                }
                                ...
                            ],
                            success_files:[
                                file_path1,
                                file_path2,
                                ...
                            ]
                            fail_files:[
                                file_path3,
                                ...
                            ]
                        }
                        ...
                    ]
        """
        from vulcanus.restful.response import BaseResponse
        from vulcanus.multi_thread_handler import MultiThreadHandler
        codeNum = 200
        codeString = "collect host config succeed"
        # Get host id list
        host_id_with_config_file = {}
        for host in real_conf_body.get('infos'):
            host_id_with_config_file[host.get('host_id')] = host.get('config_list')

        # Query host address from database
        host_ids_keys = host_id_with_config_file.keys()
        host_ids = []
        for host_id in host_ids_keys:
            host_ids.append(str(host_id))
        filters = {"host_ids": host_ids}
        query_url = f"http://{configuration.domain}{HOSTS_FILTER}?{urlencode(filters)}"
        response_data = BaseResponse.get_response(method="GET", url=query_url, data={}, header=g.headers)
        host_info_list = response_data.get("data", [])
        if not host_info_list:
            LOGGER.warning("No valid host information was found.")
            codeNum = 500
            codeString = "No valid host information was found."
            return codeNum, codeString, []

        # Get file content
        tasks = [(host, host_id_with_config_file[host["host_id"]]) for host in host_info_list]
        multi_thread = MultiThreadHandler(lambda data: Format.get_file_content(*data), tasks, None)
        multi_thread.create_thread()

        return codeNum, codeString, Format.generate_target_data_format(multi_thread.get_result(),
                                                                       host_id_with_config_file)

    @staticmethod
    def run_subprocess(cmd, result_queue):
        try:
            completed_process = subprocess.run(cmd, cwd=PARENT_DIRECTORY, shell=True, capture_output=True, text=True)
            result_queue.put(completed_process)
        except subprocess.CalledProcessError as ex:
            result_queue.put(ex)

    @staticmethod
    def ansible_handler(now_time, ansible_forks, extra_vars, HOST_FILE):
        if not os.path.exists(SYNC_LOG_PATH):
            os.makedirs(SYNC_LOG_PATH)

        SYNC_LOG = SYNC_LOG_PATH + "sync_config_" + now_time + ".log"
        cmd = f"ansible-playbook -f {ansible_forks} -e '{extra_vars}' " \
              f"-i {HOST_FILE} {SYNC_CONFIG_YML} |tee {SYNC_LOG} "
        result_queue = queue.Queue()
        thread = threading.Thread(target=Format.run_subprocess, args=(cmd, result_queue))
        thread.start()

        thread.join()
        try:
            completed_process = result_queue.get(block=False)
            if isinstance(completed_process, subprocess.CalledProcessError):
                LOGGER.error("ansible subprocess error:", completed_process)
            else:
                if completed_process.returncode == 0:
                    return completed_process.stdout
                else:
                    LOGGER.error("ansible subprocess error:", completed_process)
        except queue.Empty:
            LOGGER.error("ansible subprocess nothing result")

    @staticmethod
    def ansible_sync_domain_config_content(host_list: list, file_path_infos: list):
        # 初始化参数和响应
        now_time = str(int(time.time()))
        host_ip_sync_result = {}
        Format.generate_config(host_list, host_ip_sync_result, now_time)

        ansible_forks = len(host_list)
        # 配置文件中读取并发数量
        # 从内存中获取serial_count
        serial_count = configuration.serial.serial_count
        # 换种方式
        path_infos = {}
        for file_info in file_path_infos:
            file_path = file_info.get("file_path")
            file_content = file_info.get("content")
            # 写临时文件
            src_file_path = "/tmp/" + os.path.basename(file_path)
            with open(src_file_path, "w", encoding="UTF-8") as f:
                f.write(file_content)
            path_infos[src_file_path] = file_path

        # 调用ansible
        extra_vars = json.dumps({"serial_count": serial_count, "file_path_infos": path_infos})
        try:
            HOST_FILE = HOST_PATH_FILE + "hosts_" + now_time + ".yml"
            result = Format.ansible_handler(now_time, ansible_forks, extra_vars, HOST_FILE)
        except Exception as ex:
            LOGGER.error("ansible playbook execute error:", ex)
            return host_ip_sync_result

        processor_result = result.splitlines()
        char_to_filter = 'item='
        filtered_list = [item for item in processor_result if char_to_filter in item]
        if not filtered_list:
            return host_ip_sync_result
        for line in filtered_list:
            start_index = line.find("[") + 1
            end_index = line.find("]", start_index)
            ip_port = line[start_index:end_index]
            sync_results = host_ip_sync_result.get(ip_port)

            start_index1 = line.find("{")
            end_index1 = line.find(")", start_index1)
            path_str = line[start_index1:end_index1]
            file_path = json.loads(path_str.replace("'", "\"")).get("value")
            if line.startswith("ok:") or line.startswith("changed:"):
                signal_file_sync = {
                    "filePath": file_path,
                    "result": "SUCCESS"
                }
            else:
                signal_file_sync = {
                    "filePath": file_path,
                    "result": "FAIL"
                }
            sync_results.append(signal_file_sync)
        # 删除中间文件
        try:
            # 删除/tmp下面以id_dsa结尾的文件
            file_pattern = "*id_dsa"
            tmp_files_to_delete = glob.glob(os.path.join(KEY_FILE_PREFIX, file_pattern))
            for tmp_file_path in tmp_files_to_delete:
                os.remove(tmp_file_path)

            # 删除/tmp下面临时写的path_infos的key值文件
            for path in path_infos.keys():
                os.remove(path)

            # 删除临时的HOST_PATH_FILE的临时inventory文件
            os.remove(HOST_FILE)
        except OSError as ex:
            LOGGER.error("remove file error: %s", ex)
        return host_ip_sync_result

    @staticmethod
    def generate_config(host_list, host_ip_sync_result, now_time):
        # 取出host_ip,并传入ansible的hosts中
        hosts = {
            "all": {
                "children": {
                    "sync": {
                        "hosts": {

                        }
                    }
                }
            }
        }

        for host in host_list:
            # 生成临时的密钥key文件用于ansible访问远端主机
            key_file_path = KEY_FILE_PREFIX + host['host_ip'] + KEY_FILE_SUFFIX
            with open(key_file_path, 'w', encoding="UTF-8") as keyfile:
                os.chmod(key_file_path, 0o600)
                keyfile.write(host['pkey'])
            host_ip = host['host_ip']
            host_vars = {
                "ansible_host": host_ip,
                "ansible_ssh_user": "root",
                "ansible_ssh_private_key_file": key_file_path,
                "ansible_ssh_port": host['ssh_port'],
                "ansible_python_interpreter": "/usr/bin/python3",
                "host_key_checking": False,
                "interpreter_python": "auto_legacy_silent",
                "become": True,
                "become_method": "sudo",
                "become_user": "root",
                "become_ask_pass": False,
                "ssh_args": "-C -o ControlMaster=auto -o ControlPersist=60s StrictHostKeyChecking=no"
            }

            hosts['all']['children']['sync']['hosts'][host_ip + "_" + str(host['ssh_port'])] = host_vars
            # 初始化结果
            host_ip_sync_result[host['host_ip'] + "_" + str(host['ssh_port'])] = list()
        HOST_FILE = HOST_PATH_FILE + "hosts_" + now_time + ".yml"
        with open(HOST_FILE, 'w') as outfile:
            yaml.dump(hosts, outfile, default_flow_style=False)

    @staticmethod
    def ansible_sync_domain_config_content(host_list: list, file_path_infos: list):
        # 初始化参数和响应
        now_time = str(int(time.time()))
        host_ip_sync_result = {}
        Format.generate_config(host_list, host_ip_sync_result, now_time)

        ansible_forks = len(host_list)
        # 配置文件中读取并发数量
        # 从内存中获取serial_count
        serial_count = configuration.serial.serial_count

        # 换种方式
        path_infos = {}
        for file_info in file_path_infos:
            file_path = file_info.get("file_path")
            file_content = file_info.get("content")
            # 写临时文件
            src_file_path = "/tmp/" + os.path.basename(file_path)
            with open(src_file_path, "w", encoding="UTF-8") as f:
                f.write(file_content)
            path_infos[src_file_path] = file_path

        # 调用ansible
        extra_vars = json.dumps({"serial_count": serial_count, "file_path_infos": path_infos})
        try:
            HOST_FILE = HOST_PATH_FILE + "hosts_" + now_time + ".yml"
            result = Format.ansible_handler(now_time, ansible_forks, extra_vars, HOST_FILE)
        except Exception as ex:
            LOGGER.error("ansible playbook execute error:", ex)
            return host_ip_sync_result

        processor_result = result.splitlines()
        char_to_filter = 'item='
        filtered_list = [item for item in processor_result if char_to_filter in item]
        if not filtered_list:
            return host_ip_sync_result
        for line in filtered_list:
            start_index = line.find("[") + 1
            end_index = line.find("]", start_index)
            ip_port = line[start_index:end_index]
            sync_results = host_ip_sync_result.get(ip_port)

            start_index1 = line.find("{")
            end_index1 = line.find(")", start_index1)
            path_str = line[start_index1:end_index1]
            file_path = json.loads(path_str.replace("'", "\"")).get("value")
            if line.startswith("ok:") or line.startswith("changed:"):
                signal_file_sync = {
                    "filePath": file_path,
                    "result": "SUCCESS"
                }
            else:
                signal_file_sync = {
                    "filePath": file_path,
                    "result": "FAIL"
                }
            sync_results.append(signal_file_sync)
        # 删除中间文件
        try:
            # 删除/tmp下面以id_dsa结尾的文件
            file_pattern = "*id_dsa"
            tmp_files_to_delete = glob.glob(os.path.join(KEY_FILE_PREFIX, file_pattern))
            for tmp_file_path in tmp_files_to_delete:
                os.remove(tmp_file_path)

            # 删除/tmp下面临时写的path_infos的key值文件
            for path in path_infos.keys():
                os.remove(path)

            # 删除临时的HOST_PATH_FILE的临时inventory文件
            os.remove(HOST_FILE)
        except OSError as ex:
            LOGGER.error("remove file error: %s", ex)
        return host_ip_sync_result

    @staticmethod
    def batch_sync_config(params):
        # 初始化响应
        codeNum = 200
        codeString = "batch sync config succeed"
        file_path_infos = params.get('file_path_infos')
        host_ids = params.get('host_ids')
        sync_result = list()
        from vulcanus.restful.response import BaseResponse
        # 获取host信息
        filters = {"host_ids": host_ids}
        query_url = f"http://{configuration.domain}{HOSTS_FILTER}?{urlencode(filters)}"
        response_data = BaseResponse.get_response(method="Get", url=query_url, data={}, header=g.headers)
        host_list = response_data.get("data", [])
        if not host_list:
            LOGGER.warning("No valid host information was found.")
            codeNum = 500
            codeString = "No valid host information was found."
            return codeNum, codeString, sync_result

        # 将ip和id对应起来
        host_id_ip_dict = dict()
        if host_list:
            for host in host_list:
                key = host['host_ip'] + "_" + str(host['ssh_port'])
                host_id_ip_dict[key] = host['host_id']

        host_ip_sync_result = Format.ansible_sync_domain_config_content(host_list, file_path_infos)

        if not host_ip_sync_result:
            codeNum = 500
            codeString = "execute command error."
            return codeNum, codeString, sync_result
        # 处理成id对应结果
        for key, value in host_ip_sync_result.items():
            host_id = host_id_ip_dict.get(key)
            single_result = {
                "host_id": host_id,
                "syncResult": value
            }
            sync_result.append(single_result)
        return codeNum, codeString, sync_result

    @staticmethod
    def get_all_domain_expected_confs(params):
        from ragdoll.app.utils.yang_module import YangModule
        from ragdoll.app import TARGETDIR
        code_num = 200
        code_string = "Successfully get the expected configuration file information."
        all_domain_expected_files = []
        domain_names = params.get("domainNames")
        if len(domain_names) == 0:
            code_num = 400
            code_string = "The current domain does not exist, please create the domain first."
            return code_num, code_string, []

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
            code_num = 400
            code_string = "The current domain does not exist, please create the domain first."
            return code_num, code_string, []

        return code_num, code_string, all_domain_expected_files

    @staticmethod
    def get_cluster_all_host(cluster_id):
        from vulcanus.restful.response import BaseResponse
        # 获取host信息
        filters = {"cluster_list": [cluster_id]}
        query_url = f"http://{configuration.domain}{HOSTS_FILTER}?{urlencode(filters)}"
        response_data = BaseResponse.get_response(method="Get", url=query_url, data={}, header=g.headers)
        host_list = response_data.get("data", [])
        return host_list

    @staticmethod
    def get_cluster_domain(cluster_id):
        from ragdoll.app.proxy.domain import DomainProxy
        callback = DomainProxy()
        callback.connect()
        domain_page_filter = {"cluster_list": [cluster_id]}
        code, result = callback.get_domains_by_cluster(domain_page_filter)
        domain_list = result.get("domain_infos")
        domain_id_list = []
        if not domain_list:
            return domain_id_list
        for domain in domain_list:
            domain_id_list.append(domain.get("domain_id"))
        return domain_id_list


