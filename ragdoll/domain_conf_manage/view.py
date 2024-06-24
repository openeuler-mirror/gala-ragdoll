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
@Time: 2024/3/8 11:40
@Author: JiaoSiMao
Description:
"""
import io
import json
import os

import connexion
import requests
from flask import request
from vulcanus.restful.resp.state import PARAM_ERROR, SUCCEED, PARTIAL_SUCCEED, SERVER_ERROR
from vulcanus.restful.response import BaseResponse

from ragdoll.conf.constant import TARGETDIR
from ragdoll.const.conf_handler_const import DIRECTORY_FILE_PATH_LIST
from ragdoll.function.verify.domain_conf import AddManagementConfsSchema, UploadManagementConfsSchema, \
    DeleteManagementConfsSchema, GetManagementConfsSchema, QueryChangelogSchema
from ragdoll.log.log import LOGGER
from ragdoll.models import ConfFiles, ConfFile, ExceptedConfInfo, ConfBaseInfo
from ragdoll.utils.conf_tools import ConfTools
from ragdoll.utils.format import Format
from ragdoll.utils.git_tools import GitTools
from ragdoll.utils.object_parse import ObjectParse
from ragdoll.utils.yang_module import YangModule


class AddManagementConfsInDomain(BaseResponse):
    @BaseResponse.handle(schema=AddManagementConfsSchema, token=True)
    def post(self, **params):
        """add management configuration items and expected values in the domain

            add management configuration items and expected values in the domain # noqa: E501

            :param body: domain info
            :type body: dict | bytes

            :rtype: BaseResponse
            """
        accessToken = request.headers.get("access_token")
        domain = params.get("domainName")
        conf_files = params.get("confFiles")

        # check the input domain
        checkRes = Format.domainCheck(domain)
        if not checkRes:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum, message="Failed to verify the input parameter, please check the input "
                                                       "parameters.")

        # check whether the domain exists
        isExist = Format.isDomainExist(domain)
        if not isExist:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum, message="The current domain does not exist, please create the domain "
                                                       "first.")

        # check whether the conf_files is null
        if len(conf_files) == 0:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum, message="The path of file can't be empty")

        # Check all conf_files and check whether contents is empty. If so, the query actual configuration
        # interface is called. If not, the conversion is performed directly.
        # Content and host_id can be set to either content or host_id.
        # If they are both empty, invalid input is returned.
        contents_list_null = []
        contents_list_non_null = []
        for d_conf in conf_files:
            if "contents" in d_conf:
                contents_list_non_null.append(d_conf)
            elif d_conf["hostId"]:
                contents_list_null.append(d_conf)
            else:
                codeNum = PARAM_ERROR
                return self.response(code=codeNum, message="The input parameters are not compliant, please check the "
                                                           "input parameters.")

        successConf = []
        failedConf = []
        object_parse = ObjectParse()
        yang_module = YangModule()
        conf_tools = ConfTools()
        # Content is not an empty scene and is directly analyed and parsed
        if len(contents_list_non_null) > 0:
            for d_conf in contents_list_non_null:
                if not d_conf["contents"].strip():
                    codeNum = PARAM_ERROR
                    return self.response(code=codeNum, message="The input parameters are not compliant, please check "
                                                               "the input parameters.")
                content_string = object_parse.parse_conf_to_json(d_conf["filePath"], d_conf["contents"])
                if not content_string or not json.loads(content_string):
                    failedConf.append(d_conf["filePath"])
                else:
                    # create the file and expected value in domain
                    feature_path = yang_module.get_feature_by_real_path(domain, d_conf["filePath"])
                    result = conf_tools.wirteFileInPath(feature_path, content_string + '\n')
                    if result:
                        successConf.append(d_conf["filePath"])
                    else:
                        failedConf.append(d_conf["filePath"])

        # content is empty
        if len(contents_list_null) > 0:
            # get the real conf in host
            get_real_conf_body = {}
            get_real_conf_body_info = []
            LOGGER.debug("contents_list_null is : {}".format(contents_list_null))
            exist_host = dict()
            for d_conf in contents_list_null:
                host_id = int(d_conf["hostId"])
                if host_id in exist_host:
                    if d_conf["filePath"] not in DIRECTORY_FILE_PATH_LIST:
                        exist_host[host_id].append(d_conf["filePath"])
                    else:
                        codeNum, codeString, file_paths = object_parse.get_directory_files(d_conf, host_id, accessToken)
                        if len(file_paths) == 0:
                            return self.response(code=codeNum, message=codeString)
                        else:
                            for file_path in file_paths:
                                exist_host[host_id].append(file_path)
                else:
                    if d_conf["filePath"] not in DIRECTORY_FILE_PATH_LIST:
                        conf_list = list()
                        conf_list.append(d_conf["filePath"])
                        exist_host[host_id] = conf_list
                    else:
                        codeNum, codeString, file_paths = object_parse.get_directory_files(d_conf, host_id, accessToken)
                        if len(file_paths) == 0:
                            return self.response(code=codeNum, message=codeString)
                        else:
                            exist_host[host_id] = file_paths

            for k, v in exist_host.items():
                confs = dict()
                confs["host_id"] = k
                confs["config_list"] = v
                get_real_conf_body_info.append(confs)

            get_real_conf_body["infos"] = get_real_conf_body_info

            url = conf_tools.load_url_by_conf().get("collect_url")
            headers = {"Content-Type": "application/json", "access_token": accessToken}
            try:
                response = requests.post(url, data=json.dumps(get_real_conf_body), headers=headers)  # post request
            except requests.exceptions.RequestException as connect_ex:
                LOGGER.error(f"An error occurred: {connect_ex}")
                codeNum = PARAM_ERROR
                codeString = "Failed to obtain the actual configuration, please check the interface of config/collect."
                return self.response(code=codeNum, message=codeString)

            response_code = json.loads(response.text).get("code")
            if response_code == None:
                codeNum = PARAM_ERROR
                codeString = "Failed to obtain the actual configuration, please check the interface of conf/collect."
                return self.response(code=codeNum, message=codeString)

            if (response_code != "200") and (response_code != "206"):
                codeNum = PARAM_ERROR
                codeString = "Failed to obtain the actual configuration, please check the file exists."
                return self.response(code=codeNum, message=codeString)

            reps = json.loads(response.text).get("data")
            if not reps or len(reps) == 0:
                codeNum = PARAM_ERROR
                codeString = "Failed to obtain the actual configuration, please check the host info for conf/collect."
                return self.response(code=codeNum, message=codeString)

            directory_d_file = []
            directory_d_files = {}
            for d_res in reps:
                failedlist = d_res.get("fail_files")
                if len(failedlist) > 0:
                    for d_failed in failedlist:
                        failedConf.append(d_failed)
                    continue
                d_res_infos = d_res.get("infos")
                for d_file in d_res_infos:
                    for dir_path in DIRECTORY_FILE_PATH_LIST:
                        if str(d_file.get("path")).find(dir_path) == -1:
                            file_path = d_file.get("path")
                            content = d_file.get("content")
                            content_string = object_parse.parse_conf_to_json(file_path, content)
                            # create the file and expected value in domain
                            if not content_string or not json.loads(content_string):
                                failedConf.append(file_path)
                            else:
                                feature_path = yang_module.get_feature_by_real_path(domain, file_path)
                                result = conf_tools.wirteFileInPath(feature_path, content_string + '\n')
                                if result:
                                    successConf.append(file_path)
                                else:
                                    failedConf.append(file_path)
                        else:
                            directory_d_file.append(d_file)
                            directory_d_files[dir_path] = directory_d_file
            if len(directory_d_files) > 0:
                for dir_path, directory_d_file in directory_d_files.items():
                    content_string = object_parse.parse_dir_conf_to_json(dir_path, directory_d_file)
                    if not content_string or not json.loads(content_string):
                        failedConf.append(dir_path)
                    else:
                        feature_path = yang_module.get_feature_by_real_path(domain, dir_path)
                        result = conf_tools.wirteFileInPath(feature_path, content_string + '\n')
                        if result:
                            successConf.append(dir_path)
                        else:
                            failedConf.append(dir_path)
        # git commit message
        if len(successConf) > 0:
            git_tools = GitTools()
            succ_conf = ""
            for d_conf in successConf:
                succ_conf = succ_conf + d_conf + " "
            commit_code = git_tools.gitCommit("Add the conf in {} domian, ".format(domain) +
                                              "the path including : {}".format(succ_conf))

        # Joinin together the returned codenum and codeMessage
        LOGGER.debug("successConf is : {}".format(successConf))
        LOGGER.debug("failedConf is : {}".format(failedConf))
        if len(successConf) == 0:
            codeNum = PARAM_ERROR
            codeString = "All configurations failed to be added."
        elif len(failedConf) > 0:
            codeNum = PARTIAL_SUCCEED
            codeString = Format.splicErrorString("confs", "add management conf", successConf, failedConf)
        else:
            codeNum = SUCCEED
            codeString = Format.spliceAllSuccString("confs", "add management conf", successConf)

        return self.response(code=codeNum, message=codeString)


class UploadManagementConfsInDomain(BaseResponse):
    @BaseResponse.handle(token=True)
    def post(self, **params):
        """upload management configuration items and expected values in the domain

            upload management configuration items and expected values in the domain # noqa: E501

            :param body: file info
            :type body: FileStorage

            :rtype: BaseResponse
            """
        file = connexion.request.files['file']

        filePath = connexion.request.form.get("filePath")
        domainName = connexion.request.form.get("domainName")
        # check the input domainName
        checkRes = Format.domainCheck(domainName)
        if not checkRes:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum, message="Failed to verify the input parameter, please check the input "
                                                       "parameters.")

        # check whether the domainName exists
        isExist = Format.isDomainExist(domainName)
        if not isExist:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum, message="The current domain does not exist, please create the domain "
                                                       "first.")

        # check whether the file is null
        if file is None:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum, message="The file of conf can't be empty")

        # check whether the conf is null
        if filePath is None:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum, message="The conf body of conf can't be empty")

        successConf = []
        failedConf = []
        object_parse = ObjectParse()
        yang_module = YangModule()
        conf_tools = ConfTools()

        # content is file
        if file:
            if not filePath.strip():
                codeNum = PARAM_ERROR
                return self.response(code=codeNum, message="The input parameters are not compliant, please check the "
                                                           "input parameters.")
            try:
                file_bytes = file.read()
                if len(file_bytes) > 1024 * 1024:
                    codeNum = PARAM_ERROR
                    return self.response(code=codeNum, message="The size of the uploaded file must be less than 1MB")
                byte_stream = io.BytesIO(file_bytes)

                # Read the contents of the byte stream
                line_content = byte_stream.read().decode("UTF-8")
            except OSError as err:
                LOGGER.error("OS error: {}".format(err))
                codeNum = SERVER_ERROR
                return self.response(code=codeNum, message="OS error: {0}".format(err))
            except Exception as ex:
                LOGGER.error("Other error: {}".format(ex))
                codeNum = SERVER_ERROR
                return self.response(code=codeNum, message="read file error: {0}".format(ex))

            content_string = object_parse.parse_conf_to_json(filePath, line_content)
            if not content_string or not json.loads(content_string):
                failedConf.append(filePath)
            else:
                # create the file and expected value in domain
                feature_path = yang_module.get_feature_by_real_path(domainName, filePath)
                result = conf_tools.wirteFileInPath(feature_path, content_string + '\n')
                if result:
                    successConf.append(filePath)
                else:
                    failedConf.append(filePath)

        # git commit message
        if len(successConf) > 0:
            git_tools = GitTools()
            succ_conf = ""
            for d_conf in successConf:
                succ_conf = succ_conf + d_conf + " "
            commit_code = git_tools.gitCommit("Add the conf in {} domian, ".format(domainName) +
                                              "the path including : {}".format(succ_conf))

        # Joinin together the returned codenum and codeMessage
        LOGGER.debug("successConf is : {}".format(successConf))
        LOGGER.debug("failedConf is : {}".format(failedConf))
        if len(successConf) == 0:
            codeNum = PARAM_ERROR
            codeString = "All configurations failed to be added."
        elif len(failedConf) > 0:
            codeNum = PARTIAL_SUCCEED
            codeString = Format.splicErrorString("confs", "add management conf", successConf, failedConf)
        else:
            codeNum = SUCCEED
            codeString = Format.spliceAllSuccString("confs", "add management conf", successConf)

        return self.response(code=codeNum, message=codeString)


class DeleteManagementConfsInDomain(BaseResponse):
    @BaseResponse.handle(schema=DeleteManagementConfsSchema, token=True)
    def delete(self, **params):
        """delete management configuration items and expected values in the domain

            delete management configuration items and expected values in the domain # noqa: E501

            :param body: domain info
            :type body: dict | bytes

            :rtype: BaseResponse
            """
        #  check whether the domain exists
        domain = params.get("domainName")

        # check the input domain
        checkRes = Format.domainCheck(domain)
        if not checkRes:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum, message="Failed to verify the input parameter, please check the input "
                                                       "parameters.")

        isExist = Format.isDomainExist(domain)
        if not isExist:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum, message="The current domain does not exist")

        # Check whether path is null in advance
        conf_files = params.get("confFiles")
        if len(conf_files) == 0:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum, message="The conf_files path can't be empty")

        # Conf to record successes and failures
        successConf = []
        failedConf = []

        # Check whether path exists in the domain. There are two possible paths :
        # (1)xpath path
        # (2) configuration item
        domain_path = os.path.join(TARGETDIR, domain)
        LOGGER.debug("conf_files is : {}".format(conf_files))

        yang_modules = YangModule()
        module_lists = yang_modules.module_list
        if len(module_lists) == 0:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum, message="The yang module does not exist")

        LOGGER.debug("module_lists is : {}".format(module_lists))
        for conf in conf_files:
            module = yang_modules.getModuleByFilePath(conf["filePath"])
            features = yang_modules.getFeatureInModule(module)
            features_path = os.path.join(domain_path, "/".join(features))

            if os.path.isfile(features_path):
                LOGGER.info("It's a normal file : {}".format(features_path))
                try:
                    os.remove(features_path)
                except OSError as ex:
                    LOGGER.error("Failed to remove path, as OSError: {}".format(str(ex)))
                    break
                successConf.append(conf["filePath"])
            else:
                LOGGER.error("It's a not normal file : {}".format(features_path))
                failedConf.append(conf["filePath"])

        # git commit message
        if len(successConf) > 0:
            git_tools = GitTools()
            succ_conf = ""
            for d_conf in successConf:
                succ_conf = succ_conf + d_conf + " "
            commit_code = git_tools.gitCommit("delete the conf in {} domian, ".format(domain) +
                                              "the path including : {}".format(succ_conf))

        # Joinin together the returned codenum and codeMessage
        if len(failedConf) == 0:
            codeNum = SUCCEED
            codeString = Format.spliceAllSuccString("confs", "delete management conf", successConf)
        else:
            codeNum = PARAM_ERROR
            codeString = Format.splicErrorString("confs", "delete management conf", successConf, failedConf)
            codeString += "\n The reason for the failure is: these paths do not exist."

        return self.response(code=codeNum, message=codeString)


class GetManagementConfsInDomain(BaseResponse):
    @BaseResponse.handle(schema=GetManagementConfsSchema, token=True)
    def post(self, **params):
        """get management configuration items and expected values in the domain

            get management configuration items and expected values in the domain # noqa: E501

            :param body: domain info
            :type body: dict | bytes

            :rtype: ConfFiles
            """
        # Check whether the domain exists
        domain = params.get("domainName")

        # check the input domain
        checkRes = Format.domainCheck(domain)
        if not checkRes:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum, message="Failed to verify the input parameter, please check the input "
                                                       "parameters.")

        isExist = Format.isDomainExist(domain)
        if not isExist:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum, message="The current domain does not exist")

        # The parameters of the initial return value assignment
        # expected_conf_lists = ConfFiles(domain_name=domain, conf_files=[])
        expected_conf_lists = {"domainName": domain, "confFiles": []}

        # get the path in domain
        domainPath = os.path.join(TARGETDIR, domain)

        # When there is a file path is the path of judgment for the configuration items
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

                    # conf = ConfFile(file_path=file_path, contents=contents)
                    conf = {"filePath": file_path, "contents": contents}
                    # expected_conf_lists.conf_files.append(conf)
                    expected_conf_lists.get("confFiles").append(conf)
        LOGGER.debug("expected_conf_lists is :{}".format(expected_conf_lists))

        if len(expected_conf_lists.get("domainName")) > 0:
            codeNum = SUCCEED
            codeString = "Get management configuration items and expected values in the domain successfully"
            return self.response(code=codeNum, message=codeString, data=expected_conf_lists)

        else:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum, message="The file is Null in this domain")


class QueryChangelogOfManagementConfsInDomain(BaseResponse):
    @BaseResponse.handle(schema=QueryChangelogSchema, token=True)
    def post(self, **params):
        """query the change log of management config in domain

            query the change log of management config in domain # noqa: E501

            :param body: domain info
            :type body: dict | bytes

            :rtype: ExceptedConfInfo
            """
        #  check whether the domain exists
        domain = params.get("domainName")
        LOGGER.debug("Query changelog of conf body is : {}".format(params))

        # check the input domain
        checkRes = Format.domainCheck(domain)
        if not checkRes:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum, message="Failed to verify the input parameter, please check the input "
                                                       "parameters.")

        isExist = Format.isDomainExist(domain)
        if not isExist:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum, message="The current domain does not exist")

        # Check whether path is empty in advance. If path is empty, the configuration in the
        # entire domain is queried. Otherwise, the historical records of the specified file are queried.
        conf_files = params.get("confFiles")
        LOGGER.debug("conf_files is : {}".format(conf_files))
        conf_files_list = []
        if conf_files:
            for d_conf in conf_files:
                LOGGER.debug("d_conf is : {}".format(d_conf))
                conf_files_list.append(d_conf["filePath"])
        success_conf = []
        failed_conf = []
        domain_path = os.path.join(TARGETDIR, domain)
        # expected_conf_lists = ExceptedConfInfo(domain_name=domain, conf_base_infos=[])
        expected_conf_lists = {"domainName": domain, "confBaseInfos": []}
        yang_modules = YangModule()
        for root, dirs, files in os.walk(domain_path):
            if len(files) > 0 and len(root.split('/')) > 3:
                if "hostRecord.txt" in files:
                    continue
                for d_file in files:
                    feature = os.path.join(root.split('/')[-1], d_file)
                    d_module = yang_modules.getModuleByFeature(feature)
                    file_lists = yang_modules.getFilePathInModdule(yang_modules.module_list)
                    file_path = file_lists.get(d_module.name()).split(":")[-1]
                    if conf_files_list and (file_path not in conf_files_list):
                        continue
                    d_file_path = os.path.join(root, d_file)
                    expectedValue = Format.get_file_content_by_read(d_file_path)
                    git_tools = GitTools()
                    gitMessage = git_tools.getLogMessageByPath(d_file_path)
                    if gitMessage and expectedValue:
                        success_conf.append(file_path)
                    else:
                        failed_conf.append(file_path)

                    conf_base_info = {"filePath": file_path, "expectedContents": expectedValue, "changeLog": gitMessage}
                    expected_conf_lists.get("confBaseInfos").append(conf_base_info)

        LOGGER.debug("expected_conf_lists is : {}".format(expected_conf_lists))

        if len(success_conf) == 0:
            codeNum = SERVER_ERROR
            return self.response(code=codeNum, message="Failed to query the changelog of the configure in the domain.")
        if len(failed_conf) > 0:
            codeNum = PARAM_ERROR
        else:
            codeNum = SUCCEED

        return self.response(code=codeNum, message="Succeed to query the changelog of the configure in the domain.",
                             data=expected_conf_lists)
