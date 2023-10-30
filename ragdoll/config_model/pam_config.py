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
Time: 2023-09-04 11:23:00
Author: jiaosimao
Description: pam.d directory file config analyze
"""
from ragdoll.utils.yang_module import YangModule
from ragdoll.const.conf_handler_const import NOT_SYNCHRONIZE
from ragdoll.const.conf_handler_const import SYNCHRONIZED


class PamConfig:
    def __init__(self):
        self.conf = dict()
        self.yang = dict()

    @staticmethod
    def parse_conf_to_dict(res_infos):
        """
        将配置信息conf_info转为list，但是并未校验配置项是否合法
        """
        conf_dict_list = dict()
        for res in res_infos:
            res_path = res.get('path')
            res_content = res.get('content')
            conf_dict_list[res_path] = res_content
        return conf_dict_list

    def load_yang_model(self, yang_info):
        yang_module = YangModule()
        xpath = yang_module.getXpathInModule(yang_info)  # get all xpath in yang_info
        for d_xpath in xpath:
            real_path = d_xpath.split('/')
            section = real_path[-2]
            option = real_path[-1]
            if section not in self.yang:
                self.yang[section] = dict()
            self.yang[section][option] = None

    def read_conf(self, res_infos):
        conf_dict_dict = self.parse_conf_to_dict(res_infos)
        if conf_dict_dict:
            self.conf = conf_dict_dict

    def write_conf(self):
        content = ""
        for key, value in self.conf.items():
            if value is not None:
                content = value
        return content

    def read_json(self, conf_path, conf_json):
        """
        desc: 将json格式的配置文件内容结构化成Class conf成员。
        """
        single_conf = dict()
        single_conf[conf_path] = conf_json
        self.conf = single_conf

    @staticmethod
    def conf_compare(src_conf, dst_conf):
        """
        desc: 比较dst_conf和src_conf是否相同，dst_conf和src_conf均为序列化后的配置信息。
        return：dst_conf和src_conf相同返回SYNCHRONIZED
                dst_conf和src_conf不同返回NOT_SYNCHRONIZE
        """
        res = SYNCHRONIZED
        src_conf_line = src_conf.strip()
        dst_conf_line = dst_conf.strip()
        if src_conf_line != dst_conf_line:
            res = NOT_SYNCHRONIZE
        return res
