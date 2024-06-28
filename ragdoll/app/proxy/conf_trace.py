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
@FileName: conf_trace.py
@Time: 2024/6/26 7:55
@Author: JiaoSiMao
Description:
"""
import sqlalchemy

from vulcanus import LOGGER
from vulcanus.restful.resp.state import SUCCEED, DATABASE_DELETE_ERROR

from ragdoll.database import Domain, DomainHost, DomainConfInfo, HostConfSyncStatus
from vulcanus.database.proxy import MysqlProxy


class ConfTraceProxy(MysqlProxy):
    def __init__(self):
        """
        Instance initialization

        Args:
            configuration (Config)
            host(str)
            port(int)
        """
        MysqlProxy.__init__(self)

    def cancel_synchronize_cluster(self, cluster_id: str):
        """
        Delete cluster info in table

        Args:
            cluster_id: cluster_id id

        Returns:
            str
        """
        try:
            # 获取cluster_id下所有的domain_id
            domain_list = self.session.query(Domain).filter(Domain.cluster_id == cluster_id).all()
            domain_id_list = []
            for domain in domain_list:
                domain_id_list.append(domain.domain_id)
            # 删除domain_host domain_conf_info host_conf_sync_status
            self.session.query(DomainHost).filter(DomainHost.domain_id.in_(domain_id_list)).delete(
                synchronize_session=False)
            self.session.query(DomainConfInfo).filter(DomainConfInfo.domain_id.in_(domain_id_list)).delete(
                synchronize_session=False)
            self.session.query(HostConfSyncStatus).filter(HostConfSyncStatus.domain_id.in_(domain_id_list)).delete(
                synchronize_session=False)
            # 删除domain
            self.session.query(Domain).filter(Domain.cluster_id == cluster_id).delete(synchronize_session=False)

            self.session.commit()
            return SUCCEED
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error("delete cluster %s info fail", cluster_id)
            self.session.rollback()
            return DATABASE_DELETE_ERROR
