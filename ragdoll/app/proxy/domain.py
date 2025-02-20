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
@FileName: domain.py
@Time: 2024/5/24 11:28
@Author: JiaoSiMao
Description:
"""
import uuid

import sqlalchemy
from ragdoll.app.serialize.domain import GetDomainsPage_ResponseSchema
from ragdoll.database import Domain

from vulcanus import LOGGER
from vulcanus.database.helper import sort_and_page
from vulcanus.database.proxy import MysqlProxy
from vulcanus.restful.resp.state import (
    DATA_EXIST,
    DATABASE_DELETE_ERROR,
    DATABASE_INSERT_ERROR,
    DATABASE_QUERY_ERROR,
    SUCCEED,
)


class DomainProxy(MysqlProxy):
    def __init__(self):
        """
        Instance initialization

        Args:
            configuration (Config)
            host(str)
            port(int)
        """
        MysqlProxy.__init__(self)

    def add_domain(self, domain_info: dict) -> str:
        """
        add domain to table

        Args:
            domain_info: parameter, e.g.
                {
                    "domain_name":"aops",
                    "cluster_id": "uuid",
                }

        Returns:
            str: SUCCEED or DATABASE_INSERT_ERROR or PARAM_ERROR
        """
        try:
            # 检查是否已经存在domain
            exist_domain_info = self.session.query(Domain).filter(
                Domain.domain_name == domain_info["domain_name"]).first()
            if exist_domain_info:
                LOGGER.info(f"this domain {domain_info['domain_name']} existed")
                return DATA_EXIST
            domain = Domain(
                domain_id=str(uuid.uuid4()),
                domain_name=domain_info["domain_name"],
                cluster_id=domain_info["cluster_id"],
            )
            self.session.add(domain)
            self.session.commit()
            LOGGER.info(f"add domain {domain.domain_name} succeed")
            return SUCCEED

        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error(f"add domain {domain.domain_name} fail")
            self.session.rollback()
            return DATABASE_INSERT_ERROR

    @staticmethod
    def _get_domains_page_filters(domain_page_filter):
        """
        Generate filters

        Args:
            domain_page_filter: sorted condition info
        """
        filters = set()
        if domain_page_filter["cluster_list"]:
            filters.add(Domain.cluster_id.in_(domain_page_filter["cluster_list"]))
        return filters

    def _query_domains_page(self, domain_page_filter: dict):
        """
            Sort domain info by specified column

            Args:
                domain_page_filter: sorted condition info

            Returns:
                dict
        """
        result = {"total_count": 0, "total_page": 0, "domain_infos": []}

        filters = self._get_domains_page_filters(domain_page_filter)

        domain_query = (
            self.session.query(
                Domain.domain_id,
                Domain.domain_name,
                Domain.cluster_id,
                Domain.priority,
                Domain.sync_status
            ).filter(*filters)
        )

        result["total_count"] = domain_query.count()
        if not result["total_count"]:
            return result

        processed_domains_query, result["total_page"] = sort_and_page(
            domain_query,
            domain_page_filter["sort"],
            domain_page_filter["direction"],
            domain_page_filter["per_page"],
            domain_page_filter["page"],
        )
        result['domain_infos'] = GetDomainsPage_ResponseSchema(many=True).dump(processed_domains_query.all())

        return result

    def _query_domains(self, domain_page_filter: dict):
        """
            Sort domain info by specified column

            Args:
                domain_page_filter: sorted condition info

            Returns:
                dict
        """
        result = {"domain_infos": []}

        filters = self._get_domains_page_filters(domain_page_filter)

        domain_query = (
            self.session.query(
                Domain.domain_id,
                Domain.domain_name,
                Domain.cluster_id,
                Domain.priority
            ).filter(*filters)
        )

        result['domain_infos'] = GetDomainsPage_ResponseSchema(many=True).dump(domain_query.all())

        return result

    def get_domains(self, domain_page_filter: dict):
        """
            get domains from table

            Args:
                domain_page_filter: parameter, e.g.
                    {
                        cluster_list (list): cluster id list
                        sort (str): sort according to specified field
                        direction (str): sort direction
                        page (int): current page
                        per_page (int): count per page
                    }
            Returns:
                int: status code
                dict: query result
        """
        result = {}
        try:
            result = self._query_domains_page(domain_page_filter)
            LOGGER.debug("Query domains succeed")
            return SUCCEED, result
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error("Query domains fail")
            return DATABASE_QUERY_ERROR, result

    def get_domains_by_cluster(self, domain_page_filter: dict):
        """
            get domains from table

            Args:
                domain_page_filter: parameter, e.g.
                    {
                        cluster_list (list): cluster id list
                    }
            Returns:
                int: status code
                dict: query result
        """
        result = {}
        try:
            result = self._query_domains(domain_page_filter)
            LOGGER.debug("Query domains succeed")
            return SUCCEED, result
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error("Query domains fail")
            return DATABASE_QUERY_ERROR, result

    def delete_domain(self, domain_id: str):
        """
            Delete domain from table

            Args:
                domain_id: domain id

            Returns:
                str
        """
        try:
            domain = self.session.query(Domain).filter(Domain.domain_id == domain_id).first()
            if domain and not self.session.query(Domain).filter(Domain.domain_id == domain_id).delete():
                return DATABASE_DELETE_ERROR

            self.session.commit()
            return SUCCEED
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error("delete domain %s fail", domain_id)
            return DATABASE_DELETE_ERROR

    def update_domain_sync_status(self, domain_diff_resp):
        sync_count_data = {}
        for domain_diff in domain_diff_resp:
            domain_name = domain_diff.get("domain_name")
            sync_count_data[domain_name] = {"sync_count": 0, "no_sync_count": 0}
        for domain_diff in domain_diff_resp:
            # 1 同步 0 不同步
            domain_name = domain_diff.get("domain_name")
            sync_status = domain_diff.get("sync_status")
            if sync_status == 0:
                sync_count_data[domain_name]["no_sync_count"] += 1
            if sync_status == 1:
                sync_count_data[domain_name]["sync_count"] += 1
        for key, value in sync_count_data.items():
            domain_info = self.session.query(Domain).filter(Domain.domain_name == key).first()
            # 全部同步
            if value["sync_count"] > 0 and value["no_sync_count"] == 0:
                new_domain_data = {"domain_id": domain_info.domain_id, "sync_status": 1}
                self.session.query(Domain).filter(Domain.domain_id == domain_info.domain_id).update(new_domain_data)
            # 全部未同步
            if value["sync_count"] == 0 and value["no_sync_count"] > 0:
                new_domain_data = {"domain_id": domain_info.domain_id, "sync_status": 0}
                self.session.query(Domain).filter(Domain.domain_id == domain_info.domain_id).update(new_domain_data)
            # 未知，定位未同步
            if value["sync_count"] == 0 and value["no_sync_count"] == 0:
                new_domain_data = {"domain_id": domain_info.domain_id, "sync_status": 0}
                self.session.query(Domain).filter(Domain.domain_id == domain_info.domain_id).update(new_domain_data)
            # 有同步的，有不同步的，显示为2，部分同步
            if value["sync_count"] > 0 and value["no_sync_count"] > 0:
                new_domain_data = {"domain_id": domain_info.domain_id, "sync_status": 2}
                self.session.query(Domain).filter(Domain.domain_id == domain_info.domain_id).update(new_domain_data)
            self.session.commit()

    def sync_data(self):
        """
            Returns:
                int: status code
                float: sync_count
                int: no_sync_count
        """
        try:
            sync_count = self.session.query(Domain).filter(Domain.sync_status == 1).count()
            total_count = self.session.query(Domain).count()
            if total_count == 0:
                return SUCCEED, 0.0, 0
            no_sync_count = self.session.query(Domain).filter(Domain.sync_status == 0).count()
            sync_rate = sync_count / total_count
            return SUCCEED, sync_rate, no_sync_count, sync_count
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error("Query domains fail")
            return DATABASE_QUERY_ERROR, 0.0, 0

    def query_domain_by_name(self, domain_name: str):
        """
            Sort domain info by specified column

            Args:
                domain_name: aops

            Returns:
                dict
        """

        domain_info = self.session.query(Domain).filter(Domain.domain_name == domain_name).first()

        return domain_info

    def get_all_domains(self):
        domains = self.session.query(Domain).all()
        return domains

