import os
import logging
import re
import json
import configparser
import ast
import requests

from ragdoll.log.log import LOGGER
from ragdoll.models.base_response import BaseResponse  # noqa: E501
from ragdoll.models.conf_file import ConfFile
from ragdoll.models.conf_files import ConfFiles
from ragdoll.models.realconf_base_info import RealconfBaseInfo
from ragdoll.models.real_conf_info import RealConfInfo  # noqa: E501
from ragdoll.models.conf_is_synced import ConfIsSynced
from ragdoll.models.host_sync_status import HostSyncStatus
from ragdoll.models.sync_status import SyncStatus  # noqa: E501
from ragdoll.models.host import Host  # noqa: E501
from ragdoll.utils.host_tools import HostTools

CONFIG = "/etc/ragdoll/gala-ragdoll.conf"


class Format(object):

    @staticmethod
    def domainCheck(domainName):
        res = True
        if not re.match(r"^[A-Za-z0-9_\.-]*$", domainName) or domainName == "" or len(domainName) > 255:
            res =  False
        return res

    @staticmethod
    def isDomainExist(domainName):
        TARGETDIR = Format.get_git_dir()
        domainPath = os.path.join(TARGETDIR, domainName)
        if os.path.exists(domainPath):
            return True

        return False

    @staticmethod
    def spliceAllSuccString(obj, operation, succDomain):
        """
        docstring
        """
        codeString = "All {obj} {oper} successfully, {succ} {obj} in total.".format( \
            obj=obj, oper=operation, succ=len(succDomain))
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
    def addHostToFile(d_file, host):
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
        isHostInDomain = False
        TARGETDIR = Format.get_git_dir()
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
    def is_exists_file(d_file):
        if os.path.exists(d_file):
            return True
        elif os.path.islink(d_file):
            logging.debug("File: %s is a symlink, skipped!", d_file)
        else:
            logging.error("File: %s does not exist.", d_file)

        return False

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
            logging.error(f"File not found: {d_file}")
        except IOError as e:
            logging.error(f"IO error: {e}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")
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
        cf = configparser.ConfigParser()
        if os.path.exists(CONFIG):
            cf.read(CONFIG, encoding="utf-8")
        else:
            parent = os.path.dirname(os.path.realpath(__file__))
            conf_path = os.path.join(parent, "../../config/gala-ragdoll.conf")
            cf.read(conf_path, encoding="utf-8")
        git_dir = ast.literal_eval(cf.get("git", "git_dir"))
        return git_dir

    @staticmethod
    def get_hostinfo_by_domain(domainName):
        """
        desc: Query hostinfo by domainname
        """
        TARGETDIR = Format.get_git_dir()
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
            logging.error("OS error: {0}".format(err))
            return hostlist
        if len(hostlist) == 0:
            logging.debug("hostlist is empty : {}".format(hostlist))
        else:
            logging.debug("hostlist is : {}".format(hostlist))
        return hostlist

    @staticmethod
    def get_manageconf_by_domain(domain):
        expected_conf_lists = ConfFiles(domain_name=domain, conf_files=[])
        TARGETDIR = Format.get_git_dir()
        domainPath = os.path.join(TARGETDIR, domain)
        from ragdoll.utils.yang_module import YangModule
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
                    expected_conf_lists.conf_files.append(conf.to_dict())

        logging.debug("expected_conf_lists is :{}".format(expected_conf_lists))
        return expected_conf_lists.to_dict()

    @staticmethod
    def get_realconf_by_domain_and_host(domain, exist_host):
        res = []
        conf_files = Format.get_manageconf_by_domain(domain)

        # get the real conf in host
        conf_list = []
        from ragdoll.utils.conf_tools import ConfTools
        conf_tools = ConfTools()
        port = conf_tools.load_port_by_conf()
        for d_conf in conf_files.get("conf_files"):
            file_path = d_conf.get("file_path").split(":")[-1]
            conf_list.append(file_path)
        logging.debug("############## get the real conf in host ##############")
        get_real_conf_body = {}
        get_real_conf_body_info = []
        for d_host in exist_host:
            get_real_conf_body_infos = {}
            get_real_conf_body_infos["host_id"] = d_host
            get_real_conf_body_infos["config_list"] = conf_list
            get_real_conf_body_info.append(get_real_conf_body_infos)
        get_real_conf_body["infos"] = get_real_conf_body_info
        url = conf_tools.load_url_by_conf().get("collect_url")
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(get_real_conf_body), headers=headers)  # post request
        resp = json.loads(response.text).get("data")
        resp_code = json.loads(response.text).get("code")
        if (resp_code != "200") and (resp_code != "206"):
            return res

        if not resp or len(resp) == 0:
            return res

        success_lists = {}
        failed_lists = {}
        from ragdoll.utils.object_parse import ObjectParse
        import connexion
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

            read_conf_info = RealConfInfo(domain_name=domain,
                                          host_id=d_host_id,
                                          conf_base_infos=[])
            d_res_infos = d_res.get("infos")
            for d_file in d_res_infos:
                file_path = d_file.get("path")
                content = d_file.get("content")
                object_parse = ObjectParse()
                content_string = object_parse.parse_conf_to_json(file_path, content)
                file_atrr = d_file.get("file_attr").get("mode")
                file_owner = "({}, {})".format(d_file.get("file_attr").get("group"),
                                               d_file.get("file_attr").get("owner"))
                real_conf_base_info = RealconfBaseInfo(path=file_path,
                                                       file_path=file_path,
                                                       file_attr=file_atrr,
                                                       file_owner=file_owner,
                                                       conf_contens=content_string)
                read_conf_info.conf_base_infos.append(real_conf_base_info.to_dict())
                if len(fail_files) > 0:
                    failed_lists.get("success_conf").append(file_path)
                else:
                    success_lists.get("success_conf").append(file_path)
            res.append(read_conf_info.to_dict())
        return res

    @staticmethod
    def check_domain_param(domain):
        code_num = 200
        base_resp = None
        check_res = Format.domainCheck(domain)
        if not check_res:
            num = 400
            base_rsp = BaseResponse(num, "Failed to verify the input parameter, please check the input parameters.")
            return base_rsp, num

        # check the domian is exist
        is_exist = Format.isDomainExist(domain)
        if not is_exist:
            code_num = 404
            base_rsp = BaseResponse(code_num, "The current domain does not exist, please create the domain first.")
            return base_rsp, code_num

        # get the exist result of the host in domain
        is_host_list_exist = Format.isHostInDomain(domain)
        if not is_host_list_exist:
            code_num = 404
            base_rsp = BaseResponse(code_num, "The host information is not set in the current domain." +
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
    def _get_domain_conf(domain):
        code_num = 200
        base_resp = None
        # get the host info in domain
        LOGGER.debug("############## get the host in domain ##############")
        host_ids = Format.get_hostid_list_by_domain(domain)
        if not host_ids:
            code_num = 404
            base_rsp = BaseResponse(code_num, "The host currently controlled in the domain is empty." +
                                    "Please add host information to the domain.")
            return base_rsp, code_num, list()

        # get the managent conf in domain
        LOGGER.debug("############## get the managent conf in domain ##############")
        man_conf_res_text = Format.get_manageconf_by_domain(domain)
        manage_confs = man_conf_res_text.get("conf_files")

        if len(manage_confs) == 0:
            code_num = 404
            base_rsp = BaseResponse(code_num, "The configuration is not set in the current domain." +
                                    "Please add the configuration information first.")
            return base_rsp, code_num, list()
        return base_resp, code_num, manage_confs

    @staticmethod
    def diff_mangeconf_with_realconf(domain, real_conf_res_text, manage_confs):
        host_ids = Format.get_hostid_list_by_domain(domain)
        sync_status = SyncStatus(domain_name=domain,
                                 host_status=[])
        from ragdoll.utils.object_parse import ObjectParse
        for d_real_conf in real_conf_res_text:
            host_id = d_real_conf.get("hostID")
            host_sync_status = HostSyncStatus(host_id=host_id,
                                              sync_status=[])
            d_real_conf_base = d_real_conf.get("conf_base_infos")
            for d_conf in d_real_conf_base:
                d_conf_path = d_conf.get("filePath")

                object_parse = ObjectParse()
                conf_type = object_parse.get_conf_type_by_conf_path(d_conf_path)
                conf_model = object_parse.create_conf_model_by_type(conf_type)

                comp_res = ""
                for d_man_conf in manage_confs:
                    if d_man_conf.get("file_path").split(":")[-1] != d_conf_path:
                        continue
                    comp_res = conf_model.conf_compare(d_man_conf.get("contents"), d_conf.get("confContents"))
                conf_is_synced = ConfIsSynced(file_path=d_conf_path,
                                              is_synced=comp_res)
                host_sync_status.sync_status.append(conf_is_synced)

            sync_status.host_status.append(host_sync_status)
        return sync_status
