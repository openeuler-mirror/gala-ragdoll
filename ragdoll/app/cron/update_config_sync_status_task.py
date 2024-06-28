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
@FileName: update_config_sync_status_task.py
@Time: 2024/3/5 16:56
@Author: JiaoSiMao
Description:
"""
import json
from contextlib import contextmanager
from typing import Dict
from urllib.parse import urlencode
from ragdoll.app import configuration
from ragdoll.app.constant import DIRECTORY_FILE_PATH_LIST
from ragdoll.app.proxy.host_conf_sync_status import HostConfSyncStatusProxy

from vulcanus.database.helper import make_mysql_engine_url, create_database_engine
from vulcanus.database.proxy import MysqlProxy
from vulcanus.log.log import LOGGER
from vulcanus.restful.resp import state
from vulcanus.restful.resp.state import SUCCEED
from vulcanus.timed import TimedTask


class UpdateConfigSyncStatusTask(TimedTask):
    @staticmethod
    def get_domain_files(domain_paths: dict, expected_confs_resp: list):
        # 获取domain中要获取文件内容的文件路径
        for domain_confs in expected_confs_resp:
            domain_name = domain_confs.get("domainName")
            conf_base_infos = domain_confs.get("confBaseInfos")
            file_list = []
            if conf_base_infos:
                for conf_info in conf_base_infos:
                    file_list.append(conf_info.get("filePath"))
            domain_paths[domain_name] = file_list

    @staticmethod
    def deal_pam_d_config(host_info, directory_path):
        # 先获取/etc/pam.d下有哪些文件
        from ragdoll.app.core.ssh import execute_command_and_parse_its_result
        from ragdoll.app.core.model import ClientConnectArgs
        from vulcanus.conf.constant import CERES_OBJECT_FILE_CONF
        command = CERES_OBJECT_FILE_CONF % directory_path
        status, content = execute_command_and_parse_its_result(
            ClientConnectArgs(host_info.get("host_ip"), host_info.get("ssh_port"),
                              host_info.get("ssh_user"), host_info.get("pkey")), command)
        if status == state.SUCCEED:
            content_dict = json.loads(content)
            directory_paths = content_dict.get("resp")
            return directory_paths
        return []

    @staticmethod
    def deal_host_file_content(domain_result, host_file_content_result):
        host_id = host_file_content_result.get("host_id")
        infos = host_file_content_result.get("infos")
        file_content_list = []
        pam_d_file_list = []
        if infos:
            for info in infos:
                pam_d_file = {}
                info_path = str(info.get("path"))
                for file_path in DIRECTORY_FILE_PATH_LIST:
                    if info_path.find(file_path) == -1:
                        signal_file_content = {
                            "filePath": info.get("path"),
                            "contents": info.get("content"),
                        }
                        file_content_list.append(signal_file_content)
                    else:
                        pam_d_file[info_path] = info.get("content")
                        pam_d_file_list.append(pam_d_file)
        if pam_d_file_list:
            directory_file_dict = {}
            for file_path in DIRECTORY_FILE_PATH_LIST:
                directory_file_dict[file_path] = {}
            for path, content_list in directory_file_dict.items():
                for pam_d_file in pam_d_file_list:
                    pam_d_file_path = str(list(pam_d_file.keys())[0])
                    if path in pam_d_file_path:
                        content_list[pam_d_file_path] = pam_d_file.get(pam_d_file_path)
            for key, value in directory_file_dict.items():
                pam_d_file_content = {"filePath": key, "contents": json.dumps(value)}
                file_content_list.append(pam_d_file_content)
        if file_content_list:
            domain_result[str(host_id)] = file_content_list

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
        if status == state.SUCCEED:
            data = json.loads(content)
            data.update({"host_id": host_info["host_id"]})
            return data
        return {"host_id": host_info["host_id"], "config_file_list": file_list}

    def collect_file_infos(self, param, host_infos_result):
        # 组装host_id和要获取内容的文件列表 一一对应
        domain_result = {}
        host_id_with_config_file = {}
        for host in param.get("infos"):
            host_id_with_config_file[host.get("host_id")] = host.get("config_list")

        for host_id, file_list in host_id_with_config_file.items():
            host_info = host_infos_result.get(host_id)
            # 处理/etc/pam.d
            for file_path in DIRECTORY_FILE_PATH_LIST:
                if file_path in file_list:
                    file_list.remove(file_path)
                    object_file_paths = self.deal_pam_d_config(host_info, file_path)
                    if object_file_paths:
                        file_list.extend(object_file_paths)
            host_file_content_result = UpdateConfigSyncStatusTask.get_file_content(
                host_info, file_list
            )
            # 处理结果
            self.deal_host_file_content(domain_result, host_file_content_result)
        return domain_result

    @staticmethod
    def make_database_engine():
        engine_url = make_mysql_engine_url(configuration)
        MysqlProxy.engine = create_database_engine(
            engine_url,
            configuration.mysql.get("POOL_SIZE"),
            configuration.mysql.get("POOL_RECYCLE"),
        )

    @staticmethod
    def get_domain_host_ids(domain_list_resp, host_sync_proxy):
        domain_host_id_dict = {}
        for domain in domain_list_resp:
            domain_name = domain["domainName"]
            status, host_sync_infos = host_sync_proxy.get_domain_host_sync_status(
                domain_name
            )
            if status != SUCCEED or not host_sync_infos:
                continue
            host_ids = [host_sync["host_id"] for host_sync in host_sync_infos]
            domain_host_id_dict[domain_name] = host_ids
        return domain_host_id_dict

    @staticmethod
    def get_all_host_infos(domain_infos):
        # 根据domain_id获取所有的host id
        from ragdoll.app.proxy.domain_host import DomainHostProxy
        from ragdoll.app import cache
        from vulcanus.conf.constant import HOSTS_FILTER, ADMIN_USER
        from vulcanus.restful.response import BaseResponse
        from vulcanus import sign_data, load_private_key
        host_infos_result = {}
        domain_host_proxy = DomainHostProxy()
        domain_host_proxy.connect()
        domain_ids = []
        for domain_info in domain_infos:
            domain_id = domain_info["domain_id"]
            domain_ids.append(domain_id)
        code_num, hostlist = domain_host_proxy.get_domain_host_by_domain_id_list(domain_ids)
        if code_num != SUCCEED or not hostlist:
            LOGGER.warning("No valid host information was found.")
            return host_infos_result
        # 根据host_id获取host的信息
        host_ids = []
        for host in hostlist:
            host_ids.append(host.get("hostId"))
        filters = {"host_ids": host_ids}
        query_url = f"http://{configuration.domain}{HOSTS_FILTER}?{urlencode(filters)}"
        signature = sign_data(filters, load_private_key(cache.location_cluster.get("private_key")))
        headers = {"X-Permission": "RSA", "X-Signature": signature, "X-Cluster-Username": ADMIN_USER}
        response_data = BaseResponse.get_response(method="Get", url=query_url, data={}, header=headers)
        host_info_list = response_data.get("data", [])
        if not host_info_list:
            LOGGER.warning("No valid host information was found.")
            return host_infos_result

        for host in host_info_list:
            host_infos_result[host["host_id"]] = host
        return host_infos_result

    @staticmethod
    def compare_conf(expected_confs_resp, domain_result):
        from ragdoll.app.utils.format import Format
        from ragdoll.app.constant import NOT_SYNCHRONIZE
        expected_confs_resp_dict = Format.deal_expected_confs_resp(expected_confs_resp)
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
        return sync_result

    @staticmethod
    def update_sync_status_for_db(domain_diff_resp, host_sync_proxy):
        if domain_diff_resp:
            status, save_ids = host_sync_proxy.update_domain_host_sync_status(
                domain_diff_resp
            )
            update_result = sum(save_ids)
            if status != SUCCEED or update_result == 0:
                LOGGER.error("failed update host sync status data")
            if update_result > 0:
                LOGGER.info(
                    "update %s host sync status  basic info succeed", update_result
                )
        else:
            LOGGER.info("no host sync status data need to update")
            return

    @contextmanager
    def app_context(self):
        from ragdoll.manage import app
        with app.app_context():
            yield

    def execute(self):
        with self.app_context():
            from ragdoll.app import cache
            from ragdoll.app.proxy.domain import DomainProxy
            from ragdoll.app.utils.format import Format
            # 获取当前集群的id
            cluster_id = cache.location_cluster["cluster_id"]
            print(f"cluster_id is {cluster_id}")
            # 根据当前集群id获取domain
            domain_proxy = DomainProxy()
            domain_proxy.connect()
            # cluster_id = result["cluster_id"]
            domain_page_filter = {"cluster_list": [cluster_id]}
            code_num, domain_list_resp = domain_proxy.get_domains_by_cluster(domain_page_filter)
            if code_num != SUCCEED or not domain_list_resp["domain_infos"]:
                LOGGER.error("There is no domain with the associated cluster id")
                return

            # 根据domain获取所有的基线配置
            domain_infos = domain_list_resp["domain_infos"]
            request_domain_expected_confs = {"domainNames": []}
            request_domain_host_id = []
            for domain_info in domain_infos:
                single_domain_info = {"domainName": domain_info["domain_name"]}
                request_domain_host_id.append(single_domain_info)
                request_domain_expected_confs.get("domainNames").append(single_domain_info)
            code_num, code_string, all_domain_expected_files = Format.get_all_domain_expected_confs(
                request_domain_expected_confs)
            if code_num != 200 or not all_domain_expected_files:
                LOGGER.error("There is no domain expected files")
                return
            # 根据domain获取所有的id，从host_conf_sync_status表中读取
            host_sync_proxy = HostConfSyncStatusProxy()
            host_sync_proxy.connect()
            domain_host_id_dict = self.get_domain_host_ids(
                request_domain_host_id, host_sync_proxy
            )
            if not domain_host_id_dict:
                LOGGER.info("no host sync status data need to update")
                return

            # 获取所有admin下面的ip的信息
            host_infos_result = self.get_all_host_infos(domain_infos)
            if not host_infos_result:
                LOGGER.info("no host sync status data need to update")
                return

            # 组装参数并调用CollectConfig接口get_file_content获取文件真实内容
            domain_paths = {}
            self.get_domain_files(domain_paths, all_domain_expected_files)

            domain_result = {}
            for domain_name, host_id_list in domain_host_id_dict.items():
                data = {"infos": []}
                file_paths = domain_paths.get(domain_name)
                if file_paths:
                    for host_id in host_id_list:
                        data_info = {"host_id": host_id, "config_list": file_paths}
                        data["infos"].append(data_info)
                if data["infos"]:
                    result = self.collect_file_infos(data, host_infos_result)
                    domain_result[domain_name] = result
            # 调用ragdoll接口进行对比
            domain_diff_resp = self.compare_conf(all_domain_expected_files, domain_result)
            # 根据结果更新数据库
            self.update_sync_status_for_db(domain_diff_resp, host_sync_proxy)
