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

import json
from collections import OrderedDict as _default_dict
from ragdoll.const.conf_handler_const import NOT_SYNCHRONIZE, SYNCHRONIZED

class BaseConfig(object):
    def __init__(self):
        self.conf = _default_dict()
        self.yang = _default_dict()

    def load_yang_model(self, yang_info):
        """
        desc: 将yang_info结构化成Class BaseConfig内yang成员。
        """
        pass

    def read_conf(self, conf_info):
        """
        desc: 将配置信息conf_info结构化成class BaseConfig内conf成员。
        
        conf_info: 配置信息，str类型
        """
        pass

    def write_conf(self):
        """
        desc: 将class BaseConfig实例成员conf反结构化成配置文件文本内容。
        return: str
        """
        pass

    def read_json(self, conf_path, conf_json):
        """
        desc: 将json格式的配置文件内容结构化成Class BaseConfig内conf成员。
        """
        conf_dict = json.loads(conf_json)
        self.conf = conf_dict
    
    def conf_compare(self, dst_conf, src_conf):
        """
        desc: 比较dst_conf和src_conf是否相同，dst_conf和src_conf均为序列化后的配置信息。
        return：dst_conf和src_conf相同返回SYNCHRONIZED
                dst_conf和src_conf不同返回NOT_SYNCHRONIZE
        """
        res = SYNCHRONIZED
        dst_conf_dict = json.loads(dst_conf)
        src_conf_dict = json.loads(src_conf)

        for src_list, dst_list in zip(sorted(src_conf_dict), sorted(dst_conf_dict)):
            if str(src_conf_dict[src_list]) != str(dst_conf_dict[dst_list]):
                res = NOT_SYNCHRONIZE
                break
        return res

