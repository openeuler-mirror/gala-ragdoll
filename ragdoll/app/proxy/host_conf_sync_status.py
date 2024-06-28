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
@Time: 2024/5/31 16:47
@Author: JiaoSiMao
Description:
"""
import sqlalchemy
from ragdoll.database import Domain, HostConfSyncStatus

from vulcanus.database.proxy import MysqlProxy
from vulcanus.restful.resp.state import SUCCEED, DATABASE_INSERT_ERROR, DATABASE_DELETE_ERROR, DATABASE_QUERY_ERROR
from vulcanus.log.log import LOGGER

class HostConfSyncStatusProxy(MysqlProxy):
    def __init__(self):
        """
        Instance initialization

        Args:
            configuration (Config)
            host(str)
            port(int)
        """
        MysqlProxy.__init__(self)

    def add_host_sync_status(self, domain_name: str, host_infos: list) -> str:
        """
        add host sync status to table

        Args:
            domain_name: test
            host_infos: parameter, e.g.
                [
                    {
                        "host_id":"xxx",
                        "host_ip": "127.0.0.1",
                    }
                ]

        Returns:
            str: SUCCEED or DATABASE_INSERT_ERROR or PARAM_ERROR
        """
        try:
            domain_info = self.session.query(Domain).filter(Domain.domain_name == domain_name).first()
            host_sync_status_to_add = []
            for host_info in host_infos:
                host_sync_status = HostConfSyncStatus(
                    host_id=host_info["host_id"],
                    host_ip=host_info["host_ip"],
                    cluster_id=domain_info.cluster_id,
                    domain_id=domain_info.domain_id,
                    sync_status=0
                )
                host_sync_status_to_add.append(host_sync_status)
            self.session.add_all(host_sync_status_to_add)
            self.session.commit()
            LOGGER.info(f"add host sync status succeed")
            return SUCCEED
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error(f"add host sync status fail")
            self.session.rollback()
            return DATABASE_INSERT_ERROR

    def delete_host_sync_status(self, domain_name: str, hostInfos: list):
        """
            Delete host sync status from table

            Args:
                domain_name: test
                hostInfos: parameter, e.g.
                [
                    {
                        "host_id":"xxx",
                    }
                ]

            Returns:
                str
        """
        try:
            domain_info = self.session.query(Domain).filter(Domain.domain_name == domain_name).first()
            delete_host_sync_status_list = []
            for hostInfo in hostInfos:
                delete_host_sync_status_list.append(hostInfo["host_id"])
            host_status_to_delete = self.session.query(HostConfSyncStatus).filter(
                HostConfSyncStatus.domain_id == domain_info.domain_id).filter(
                HostConfSyncStatus.host_id.in_(delete_host_sync_status_list))
            host_status_to_delete.delete(synchronize_session=False)
            self.session.commit()
            return SUCCEED
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error("delete domain %s fail", hostInfos)
            return DATABASE_DELETE_ERROR

    def get_domain_host_sync_status(self, domain_name: str):
        try:
            domain_info = self.session.query(Domain).filter(Domain.domain_name == domain_name).first()
            host_sync_status = self.session.query(HostConfSyncStatus). \
                filter(HostConfSyncStatus.domain_id == domain_info.domain_id).all()
            result = []
            for host_sync in host_sync_status:
                single_host_sync_status = {
                    "host_id": host_sync.host_id,
                    "host_ip": host_sync.host_ip,
                    "sync_status": host_sync.sync_status
                }
                result.append(single_host_sync_status)
            self.session.commit()
            LOGGER.debug("query host sync status %s basic info succeed", result)
            return SUCCEED, result
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            return DATABASE_QUERY_ERROR, []

    def update_domain_host_sync_status(self, domain_diff_resp: list):
        try:
            saved_ids = []

            for domain_diff in domain_diff_resp:
                domain_name = domain_diff.get("domain_name")
                host_id = domain_diff.get("host_id")
                domain_info = self.session.query(Domain).filter(Domain.domain_name == domain_name).first()
                new_domain_sync_status_data = {"domain_id": domain_info.domain_id, "host_id": host_id,
                                               "sync_status": domain_diff.get("sync_status")}
                update_count = self.session.query(HostConfSyncStatus).filter(
                    HostConfSyncStatus.host_id == domain_diff.get("host_id")). \
                    filter(HostConfSyncStatus.domain_id == domain_info.domain_id).update(new_domain_sync_status_data)
                saved_ids.append(update_count)
                self.session.commit()
                LOGGER.debug("update host sync status { %s, %s }basic info succeed", host_id, domain_name)
            if saved_ids:
                return SUCCEED, saved_ids
            return DATABASE_QUERY_ERROR, []
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            return DATABASE_QUERY_ERROR, []
