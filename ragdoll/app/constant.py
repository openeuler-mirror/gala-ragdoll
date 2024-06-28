#!/usr/bin/python3
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
"""
Time:
Author:
Description: manager constant
"""
import re

NOT_SYNCHRONIZE = "NOT SYNCHRONIZE"
SYNCHRONIZED = "SYNCHRONIZED"
LIMITS_DOMAIN_RE = re.compile('(^[*]$)|(^[@|0-9A-Za-z]+[0-9A-Za-z]$)')
LIMITS_TYPE_VALUE = "soft|hard|-|"
LIMITS_ITEM_VALUE = "core|data|fsize|memlock|nofile|rss|stack|cpu|nproc|as|maxlogins|maxsyslogins|priority|locks|sigpending|" \
                    "msgqueue|nice|rtprio|"
RESOLV_KEY_VALUE = "nameserver|domain|search|sortlist|"
FSTAB_COLUMN_NUM = 6
PAM_FILE_PATH = "/etc/pam.d"
DIRECTORY_FILE_PATH_LIST = ["/etc/pam.d"]

# ansible sync config
PARENT_DIRECTORY = "/opt/aops/ansible_task/"
HOST_PATH_FILE = "/opt/aops/ansible_task/inventory/"
SYNC_CONFIG_YML = "/opt/aops/ansible_task/playbook_entries/sync_config.yml"
CONF_TRACE_YML = "/opt/aops/ansible_task/playbook_entries/conf_trace.yml"
SYNC_LOG_PATH = "/var/log/aops/sync/"
CONF_TRACE_LOG_PATH = "/var/log/aops/conftrace/"
KEY_FILE_PREFIX = "/tmp/"
KEY_FILE_SUFFIX = "_id_dsa"
IP_START_PATTERN = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"

# crontab yml
TIMED_TASK_CONFIG_PATH = "/etc/aops/ragdoll_crontab.yml"

yang_conf_list = [
    "/etc/yum.repos.d/openEuler.repo",
    "/etc/coremail/coremail.conf",
    "/etc/ssh/sshd_config",
    "/etc/ssh/ssh_config",
    "/etc/sysctl.conf",
    "/etc/ntp.conf",
    "/etc/passwd",
    "/etc/sudoers",
    "/etc/shadow",
    "/etc/group",
    "/etc/hostname",
    "/etc/fstab",
    "/etc/ld.so.conf",
    "/etc/security/limits.conf",
    "/etc/resolv.conf",
    "/etc/rc.local",
    "/etc/bashrc",
    "/etc/profile",
    "/etc/hosts",
    "/etc/pam.d"
]
