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
@FileName: conftrace_tools.py
@Time: 2024/12/9 14:40
@Author: JiaoSiMao
Description:
"""
import glob
import os
import queue
import subprocess
import threading
import time
import yaml

from vulcanus import LOGGER
from vulcanus.restful.resp.state import SUCCEED, SERVER_ERROR

from ragdoll.app import configuration
from ragdoll.app.constant import KEY_FILE_PREFIX, KEY_FILE_SUFFIX, HOST_PATH_FILE, CONF_TRACE_LOG_PATH, \
    PARENT_DIRECTORY, CONF_TRACE_YML


class ConfTraceTools(object):
    @staticmethod
    def parse_result(action, result, host_ip_trace_result, HOST_FILE):
        code_num = SUCCEED
        code_string = f"{action} ragdoll-filetrace succeed"
        processor_result = result.splitlines()
        char_to_filter = 'unreachable='
        filtered_list = [item for item in processor_result if char_to_filter in item]
        if not filtered_list:
            code_num = SERVER_ERROR
            code_string = f"{action} ragdoll-filetrace error, no result"
        for line in filtered_list:
            result_start_index = line.find(":")
            ip_port = line[0:result_start_index]
            trace_result = host_ip_trace_result.get(ip_port.strip())
            LOGGER.info(f"Trace result for {ip_port}: {trace_result}")
            result_str = line[result_start_index:]
            if "unreachable=0" in result_str and "failed=0" in result_str:
                host_ip_trace_result[ip_port.strip()] = True
            else:
                host_ip_trace_result[ip_port.strip()] = False

        # 删除中间文件
        try:
            # 删除/tmp下面以id_dsa结尾的文件
            dsa_file_pattern = "*id_dsa"
            dsa_tmp_files_to_delete = glob.glob(os.path.join(KEY_FILE_PREFIX, dsa_file_pattern))
            for dsa_tmp_file_path in dsa_tmp_files_to_delete:
                os.remove(dsa_tmp_file_path)

            # 删除临时的HOST_PATH_FILE的临时inventory文件
            os.remove(HOST_FILE)
        except OSError as ex:
            LOGGER.error("remove file error: %s", ex)
        return code_num, code_string

    @staticmethod
    def run_subprocess(cmd, result_queue):
        try:
            completed_process = subprocess.run(cmd, cwd=PARENT_DIRECTORY, shell=True, capture_output=True, text=True)
            result_queue.put(completed_process)
        except subprocess.CalledProcessError as ex:
            result_queue.put(ex)

    @staticmethod
    def ansible_handler(now_time, ansible_forks, extra_vars, HOST_FILE):
        if not os.path.exists(CONF_TRACE_LOG_PATH):
            os.makedirs(CONF_TRACE_LOG_PATH)

        CONF_TRACE_LOG = CONF_TRACE_LOG_PATH + "conf_trace_" + now_time + ".log"

        cmd = f"ansible-playbook -f {ansible_forks} -e '{extra_vars}' " \
              f"-i {HOST_FILE} {CONF_TRACE_YML} |tee {CONF_TRACE_LOG} "
        result_queue = queue.Queue()
        thread = threading.Thread(target=ConfTraceTools.run_subprocess, args=(cmd, result_queue))
        thread.start()

        thread.join()
        try:
            completed_process = result_queue.get(block=False)
            if isinstance(completed_process, subprocess.CalledProcessError):
                LOGGER.error("ansible subprocess error:", completed_process)
                return completed_process.stdout
            else:
                if completed_process.returncode == 0:
                    return completed_process.stdout
                else:
                    LOGGER.error("ansible subprocess error:", completed_process)
                    return completed_process.stdout
        except queue.Empty:
            LOGGER.error("ansible subprocess nothing result")
            return completed_process.stdout

    @staticmethod
    def generate_config(host_list, now_time, host_ip_trace_result):
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
                keyfile.write("\n")
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
                "ssh_args": "-C -o ControlMaster=auto -o ControlPersist=60s StrictHostKeyChecking=no",
                "host_id": host['host_id']
            }

            hosts['all']['children']['sync']['hosts'][host_ip + "_" + str(host['ssh_port'])] = host_vars
            # 初始化结果
            host_ip_trace_result[host['host_ip'] + "_" + str(host['ssh_port'])] = True

        HOST_FILE = HOST_PATH_FILE + "hosts_" + now_time + ".yml"
        with open(HOST_FILE, 'w') as outfile:
            yaml.dump(hosts, outfile, default_flow_style=False)

    @staticmethod
    def ansible_conf_trace_mgmt(host_list: list, action: str, conf_files, domain_name: str):
        now_time = str(int(time.time()))
        host_ip_trace_result = {}
        ConfTraceTools.generate_config(host_list, now_time, host_ip_trace_result)
        ansible_forks = len(host_list)
        # 组装ansible执行的extra参数
        ip = configuration.domain
        port = configuration.uwsgi.port
        if conf_files:
            conf_list_str = ",".join(conf_files)
        else:
            conf_list_str = ""
        extra_vars = f"action={action} ip={ip} port={port} conf_list_str={conf_list_str} " \
                     f"domain_name={domain_name} "
        # 调用ansible
        try:
            HOST_FILE = HOST_PATH_FILE + "hosts_" + now_time + ".yml"
            result = ConfTraceTools.ansible_handler(now_time, ansible_forks, extra_vars, HOST_FILE)
        except Exception as ex:
            LOGGER.error("ansible playbook execute error:", ex)
            conf_trace_mgmt_result = "ragdoll-filetrace ansible playbook execute error"
            return SERVER_ERROR, conf_trace_mgmt_result, host_ip_trace_result
        # 根据action解析每个result
        code_num, code_string = ConfTraceTools.parse_result(action, result, host_ip_trace_result, HOST_FILE)
        return code_num, code_string, host_ip_trace_result
