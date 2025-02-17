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
from urllib.parse import urlencode

from flask import g
from vulcanus import LOGGER
from vulcanus.restful.resp import state
from vulcanus.restful.resp.state import SUCCEED, SERVER_ERROR
from vulcanus.restful.response import BaseResponse

from ragdoll.app import configuration
from ragdoll.app.proxy.conf_trace import ConfTraceProxy

from ragdoll.app.serialize.conf_trace import ConfTraceDataSchema, ConfTraceQuerySchema, ConfChangeRecordSchema
from ragdoll.app.utils.format import Format

"""
@FileName: conftrace_manage.py
@Time: 2024/12/9 10:27
@Author: JiaoSiMao
Description:
"""


class ConfTraceData(BaseResponse):
    @staticmethod
    def validate_conf_trace_info(params: dict):
        """
        query conf trace info, validate that the host sync status info is valid
        return host object

        Args:
            params (dict): e.g
            {
                "domain_name": "aops",
                "host_id": 1,
                "conf_name": "/etc/hostname",
                "info": ""
            }

        Returns:
            tuple:
                status code, host sync status object
        """
        host_info_list = Format.query_host_info([params.get("host_id")])
        if not host_info_list:
            LOGGER.warning("No valid host information was found.")
            return state.NO_DATA, []

        return state.SUCCEED, host_info_list

    @BaseResponse.handle(schema=ConfTraceDataSchema, proxy=ConfTraceProxy, token=False)
    def post(self, callback: ConfTraceProxy, **params):
        # 校验hostId是否存在
        code_num, result_list = self.validate_conf_trace_info(params)
        if code_num != SUCCEED or len(result_list) == 0:
            return self.response(code=SERVER_ERROR, message="request param host id does not exist")

        status_code = callback.add_conf_trace_info(params)
        if status_code != state.SUCCEED:
            return self.response(code=SERVER_ERROR, message="Failed to upload data, service error")
        else:
            # 按照host_id 和 file判断当天是否存在修改记录，有就不发短信了，没有就发
            code, confTraceInfos = callback.find_conf_trace_info_day(params)
            # 发送短信
            if len(confTraceInfos) <= 1:
                Format.give_alarm(params)
        return self.response(code=SUCCEED, message="Succeed to upload conf trace info data")


class ConfTraceQuery(BaseResponse):
    @BaseResponse.handle(schema=ConfTraceQuerySchema, proxy=ConfTraceProxy, token=True)
    def post(self, callback: ConfTraceProxy, **params):
        status_code, result = callback.query_conf_trace_info(params)
        if status_code != SUCCEED:
            return self.response(code=SERVER_ERROR, message="Failed to query data, service error")
        return self.response(code=SUCCEED, message="Succeed to query conf trace info data", data=result)


class ConfChangeRecordQuery(BaseResponse):
    @BaseResponse.handle(schema=ConfChangeRecordSchema, proxy=ConfTraceProxy, token=True)
    def get(self, callback: ConfTraceProxy, **params):
        status_code, result = callback.query_conf_change_record(params)
        if status_code != SUCCEED:
            return self.response(code=SERVER_ERROR, message="Failed to query data, service error")
        return self.response(code=SUCCEED, message="Succeed to query conf change record data", data=result)