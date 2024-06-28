# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2021-2021. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN 'AS IS' BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************/
import importlib
import json
from urllib.parse import urlencode

import requests
from flask import g
from ragdoll.app.constant import DIRECTORY_FILE_PATH_LIST
from ragdoll.app.utils.yang_module import YangModule

from vulcanus.conf.constant import HOSTS_FILTER
from vulcanus.log.log import LOGGER
from vulcanus.restful.resp.state import SUCCEED

BASE_PATH = "ragdoll.app.config_model."
CONFIG_MODEL_NAME = "Config"
PROJECT_NAME = "_config"


class ObjectParse(object):
    def __init__(self):
        self._yang_modules = YangModule()

    def create_conf_model_by_type(self, conf_type):
        """
        desc: Create a structured model corresponding to the configuration type.

        example:
            param: conf_type: ini
            return: IniConfig()
        """
        conf_model = ""
        project_name = conf_type + PROJECT_NAME  # example: ini_config
        project_path = BASE_PATH + project_name  # example: ragdoll.config_model.ini_config
        model_name = conf_type.capitalize() + CONFIG_MODEL_NAME  # example: IniConfig

        try:
            project = importlib.import_module(project_path)
        except ImportError:
            conf_model = ""
        else:
            _conf_model_class = getattr(project, model_name, None)  # example: IniConfig
            if _conf_model_class:
                conf_model = _conf_model_class()  # example: IniConfig()

        return conf_model

    def get_conf_type_by_conf_path(self, conf_path):
        yang_model = self._yang_modules.getModuleByFilePath(conf_path)
        if not yang_model:
            return ""
        _conf_type = self._yang_modules.getTypeInModdule([yang_model])
        conf_type = _conf_type[yang_model.name()]
        return conf_type

    def parse_model_to_json(self, d_model):
        """
        desc: convert object to json.
        """
        conf_json = ""

        conf_dict = d_model.conf
        conf_json = json.dumps(conf_dict, indent=4, ensure_ascii=False)

        return conf_json

    def parse_conf_to_json(self, conf_path, conf_info):
        """
        desc: parse the conf contents to the json accroding the yang file.
        """
        conf_type = self.get_conf_type_by_conf_path(conf_path)
        if not conf_type:
            return ""

        # create conf model
        conf_model = self.create_conf_model_by_type(conf_type)

        # load yang model info
        yang_info = self._yang_modules.getModuleByFilePath(conf_path)
        conf_model.load_yang_model(yang_info)

        # load conf info
        if conf_type == "kv":
            spacer_type = self._yang_modules.getSpacerInModdule([yang_info])
            conf_model.read_conf(conf_info, spacer_type, yang_info)
        else:
            conf_model.read_conf(conf_info)

        # to json
        conf_json = self.parse_model_to_json(conf_model)

        return conf_json

    def parse_directory_single_conf_to_json(self, conf_info, directory_path):
        """
        desc: parse the conf contents to the json accroding the yang file.
        """
        conf_type = self.get_conf_type_by_conf_path(directory_path)
        if not conf_type:
            return ""

        # create conf model
        conf_model = self.create_conf_model_by_type(conf_type)

        # load yang model info
        yang_info = self._yang_modules.getModuleByFilePath(directory_path)
        conf_model.load_yang_model(yang_info)

        # load conf info
        conf_model.read_conf(conf_info)
        # to json
        conf_json = self.parse_model_to_json(conf_model)
        return conf_json

    def parse_dir_conf_to_json(self, dir_path, res_infos):
        """
        desc: parse the conf contents to the json accroding the yang file.
        """
        conf_type = self.get_conf_type_by_conf_path(dir_path)
        if not conf_type:
            return ""

        # create conf model
        conf_model = self.create_conf_model_by_type(conf_type)

        # load yang model info
        yang_info = self._yang_modules.getModuleByFilePath(dir_path)
        conf_model.load_yang_model(yang_info)

        # load conf info
        conf_model.read_conf(res_infos)
        # to json
        conf_json = self.parse_model_to_json(conf_model)
        return conf_json

    def parse_json_to_conf(self, conf_path, json_list):
        """
        desc: 将json格式的配置信息解析成原始配置文件格式

        """
        conf_type = ""
        yang_info = ""
        spacer_info = ""
        for dir_path in DIRECTORY_FILE_PATH_LIST:
            if str(conf_path).find(dir_path) != -1:
                conf_type = self.get_conf_type_by_conf_path(dir_path)
                break
            else:
                conf_type = self.get_conf_type_by_conf_path(conf_path)
                yang_info = self._yang_modules.getModuleByFilePath(conf_path)
                spacer_info = self._yang_modules.getSpacerInModdule([yang_info])
                break

        # create conf model
        conf_model = self.create_conf_model_by_type(conf_type)

        # load conf info(json) to model
        conf_model.read_json(conf_path, json_list)

        if conf_type == "sshd":
            conf_info = conf_model.write_conf(spacer_info)
        elif conf_type == "kv":
            conf_info = conf_model.write_conf(spacer_info, yang_info)
        else:
            # to content
            conf_info = conf_model.write_conf()

        return conf_info

    def get_directory_files(self, host_id):
        try:
            from vulcanus.restful.response import BaseResponse
            from ragdoll.app import configuration
            from vulcanus.conf.constant import CERES_OBJECT_FILE_CONF
            from ragdoll.app.core.ssh import execute_command_and_parse_its_result
            from ragdoll.app.core.model import ClientConnectArgs
            # 根据host_id获取host的信息
            host_ids = [host_id]
            filters = {"host_ids": host_ids}
            query_url = f"http://{configuration.domain}{HOSTS_FILTER}?{urlencode(filters)}"
            response_data = BaseResponse.get_response(method="Get", url=query_url, data={}, header=g.headers)
            host_info_list = response_data.get("data", [])
            if not host_info_list:
                LOGGER.warning("No valid host information was found.")
                codeNum = 500
                codeString = "No valid host information was found."
                return codeNum, codeString, []
            # 根据host信息，去ssh到主机，获取主机中的目录文件列表
            host_info = host_info_list[0]
            connect_args = ClientConnectArgs(host_ip=host_info.get("host_ip"), ssh_user=host_info.get("ssh_user"),
                                             ssh_port=host_info.get("ssh_port"), pkey=host_info.get("pkey"))
            code_num, result = execute_command_and_parse_its_result(connect_args, command=CERES_OBJECT_FILE_CONF)

        except requests.exceptions.RequestException as connect_ex:
            LOGGER.error(f"An error occurred: {connect_ex}")
            codeNum = 500
            codeString = "Failed to get object dir files, please check the interface of conf/objectFile."
            return codeNum, codeString, []
        if code_num == SUCCEED:
            content_res = json.loads(result)
            if content_res.get("resp"):
                codeNum = 200
                codeString = "Success get pam.d file paths."
                return codeNum, codeString, content_res.get("resp")
        else:
            codeNum = 500
            codeString = "Failed to obtain the actual configuration, please check the host info for conf/objectFile."
            return codeNum, codeString, []
