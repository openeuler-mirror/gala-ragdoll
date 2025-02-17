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
@FileName: statistics.py
@Time: 2024/12/12 9:07
@Author: JiaoSiMao
Description:
"""
from vulcanus.restful.resp.state import SUCCEED
from vulcanus.restful.response import BaseResponse

from ragdoll.app.proxy.domain import DomainProxy


class Statistics(BaseResponse):
    @BaseResponse.handle(proxy=DomainProxy)
    def get(self, callback: DomainProxy):
        """
        create domain

        Args:
            args (dict): e.g
            {
                "domainName":"xxx",
                "priority":""
            }

        Returns:
            dict: response body
        """
        domain_sync_data = {"domain_sync_rate": 0.0, "no_sync_domain_count": 0, "sync_domain_count": 0}
        codeNum, sync_rate, no_sync_count, sync_count = callback.sync_data()
        domain_sync_data["domain_sync_rate"] = sync_rate
        domain_sync_data["no_sync_domain_count"] = no_sync_count
        domain_sync_data["sync_domain_count"] = sync_count
        if codeNum != SUCCEED:
            return self.response(code=codeNum, message="domain sync data statistics error")
        return self.response(code=codeNum, message="domain sync data statistics succeed", data=domain_sync_data)
