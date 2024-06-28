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
@FileName: host_conf_sync_status.py
@Time: 2024/6/14 15:51
@Author: JiaoSiMao
Description:
"""
from vulcanus.restful.resp.state import PARAM_ERROR

from ragdoll.app.proxy.host_conf_sync_status import HostConfSyncStatusProxy
from ragdoll.app.serialize.host_conf_sync_status import GetHostConfSyncStatusSchema
from ragdoll.app.utils.format import Format
from vulcanus.restful.response import BaseResponse
from vulcanus.log.log import LOGGER


class GetHostConfSyncStatus(BaseResponse):
    @BaseResponse.handle(schema=GetHostConfSyncStatusSchema, proxy=HostConfSyncStatusProxy)
    def post(self, callback: HostConfSyncStatusProxy, **params):
        """get host by domainName

            get the host information of the configuration domain # noqa: E501

            :param body: domain info
            :type body: dict | bytes

            :rtype: List[Host]
            """
        domain = params.get("domainName")
        # check the input domain
        checkRes = Format.domainCheck(domain)
        if not checkRes:
            codeNum = PARAM_ERROR
            return self.response(code=codeNum,
                                 message="Failed to verify the input parameter, please check the input parameters.")

        # 从数据库中读取数据
        codeNum, host_conf_sync_list = callback.get_domain_host_sync_status(domain)
        # Joining together the returned codeNum codeMessage
        if len(host_conf_sync_list) == 0:
            return self.response(code=codeNum, message="Some unknown problems.")
        else:
            LOGGER.debug("hostlist is : {}".format(host_conf_sync_list))
            return self.response(code=codeNum, message="Get host conf sync status in the domain successfully",
                                 data=host_conf_sync_list)
