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
@FileName: domain_host.py
@Time: 2024/5/24 11:28
@Author: JiaoSiMao
Description:
"""

import sqlalchemy
from ragdoll.database import Domain, DomainHost

from vulcanus import LOGGER
from vulcanus.database.proxy import MysqlProxy
from vulcanus.restful.resp.state import (
    DATABASE_DELETE_ERROR,
    DATABASE_INSERT_ERROR,
    SUCCEED, DATABASE_QUERY_ERROR,
)


class DomainHostProxy(MysqlProxy):
    def __init__(self):
        """
        Instance initialization

        Args:
            configuration (Config)
            host(str)
            port(int)
        """
        MysqlProxy.__init__(self)

    def add_domain_hosts(self, domain_name: str, host_infos: list) -> str:
        """
        add domain to table

        Args:
            domain_name: test
            host_infos: parameter, e.g.
                [
                    {
                        "hostId":"xxx",
                        "ip": "127.0.0.1",
                        "ipv6": "ipv4"
                    }
                ]

        Returns:
            str: SUCCEED or DATABASE_INSERT_ERROR or PARAM_ERROR
        """
        try:
            domain_info = self.session.query(Domain).filter(Domain.domain_name == domain_name).first()
            domain_hosts_to_add = []
            for host_info in host_infos:
                domain_host = DomainHost(
                    host_id=host_info["hostId"],
                    host_ip=host_info["ip"],
                    ipv6=host_info["ipv6"],
                    domain_id=str(domain_info.domain_id),
                )
                domain_hosts_to_add.append(domain_host)
            self.session.add_all(domain_hosts_to_add)
            self.session.commit()
            LOGGER.info(f"add domain host succeed")
            return SUCCEED
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error(f"add domain host fail")
            self.session.rollback()
            return DATABASE_INSERT_ERROR

    def delete_domain_host(self, domain_name: str, hostInfos: list):
        """
            Delete domain from table

            Args:
                domain_name: test
                hostInfos: parameter, e.g.
                [
                    {
                        "hostId":"xxx",
                    }
                ]

            Returns:
                str
        """
        try:
            domain_info = self.session.query(Domain).filter(Domain.domain_name == domain_name).first()
            delete_host_list = []
            for hostInfo in hostInfos:
                delete_host_list.append(hostInfo["hostId"])
            domain_host_to_delete = self.session.query(DomainHost).filter(
                DomainHost.domain_id == domain_info.domain_id).filter(
                DomainHost.host_id.in_(delete_host_list))
            domain_host_to_delete.delete(synchronize_session=False)
            self.session.commit()
            return SUCCEED
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error("delete domain %s fail", hostInfos)
            return DATABASE_DELETE_ERROR

    def get_domain_host_by_domain(self, domain_name: str):
        """
            get domain host from table

            Args:
                domain_name: test
            Returns:
                list
        """
        hostlist = []
        try:
            domain_info = self.session.query(Domain).filter(Domain.domain_name == domain_name).first()
            domain_host_infos = self.session.query(DomainHost).filter(
                DomainHost.domain_id == domain_info.domain_id).all()
            for domain_host in domain_host_infos:
                host = {"hostId": domain_host.host_id, "ip": domain_host.host_ip, "ipv6": domain_host.ipv6}
                hostlist.append(host)
            return SUCCEED, hostlist
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error("query domain host fail")
            return DATABASE_QUERY_ERROR, hostlist

    def get_domain_host_by_domain_id_list(self, domain_ids: list):
        """
            get domain host from table

            Args:
                domain_ids: ["xxx"]
            Returns:
                list
        """
        hostlist = []
        try:
            domain_host_infos = self.session.query(DomainHost).filter(
                DomainHost.domain_id.in_(domain_ids)).all()
            for domain_host in domain_host_infos:
                host = {"hostId": domain_host.host_id, "ip": domain_host.host_ip, "ipv6": domain_host.ipv6}
                hostlist.append(host)
            return SUCCEED, hostlist
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error("query domain host fail")
            return DATABASE_QUERY_ERROR, hostlist
