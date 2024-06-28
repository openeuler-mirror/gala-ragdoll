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
                Domain.priority
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
