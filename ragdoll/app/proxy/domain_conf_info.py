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
@FileName: domain_conf_info.py
@Time: 2024/5/24 11:29
@Author: JiaoSiMao
Description:
"""
import sqlalchemy
from ragdoll.database import Domain, DomainConfInfo

from vulcanus import LOGGER
from vulcanus.database.proxy import MysqlProxy
from vulcanus.restful.resp.state import SUCCEED, DATABASE_INSERT_ERROR, DATABASE_DELETE_ERROR, DATABASE_QUERY_ERROR


class DomainConfInfoProxy(MysqlProxy):
    def __init__(self):
        """
        Instance initialization

        Args:
            configuration (Config)
            host(str)
            port(int)
        """
        MysqlProxy.__init__(self)

    def add_domain_conf(self, domain, file_path_contents):
        """
            add domain conf to table

            Args:
                domain: test
                file_path_contents: parameter, e.g.
                    {
                        "/etc/hostname": "aops"
                    }
            Returns:
                str: SUCCEED or DATABASE_INSERT_ERROR or PARAM_ERROR
        """
        try:
            domain_info = self.session.query(Domain).filter(Domain.domain_name == domain).first()
            for path, value in file_path_contents.items():
                insert_or_update_domain_conf = DomainConfInfo(
                    domain_id=str(domain_info.domain_id),
                    conf_path=path,
                    conf_info=value
                )
                domain_conf = self.session.query(DomainConfInfo).filter(
                    DomainConfInfo.domain_id == str(domain_info.domain_id)). \
                    filter(DomainConfInfo.conf_path == path).first()
                if domain_conf:
                    domain_conf.conf_info = value
                else:
                    self.session.add(insert_or_update_domain_conf)
            self.session.commit()
            LOGGER.info(f"add domain host succeed")
            return SUCCEED
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error(f"add domain host fail")
            self.session.rollback()
            return DATABASE_INSERT_ERROR

    def delete_domain_confs(self, domain_name, domain_files):
        """
            Delete domain conf from table

            Args:
                domain_name: test
                domain_files: parameter, e.g.
                [
                    {
                        "filePath":"/etc/hostname",
                    }
                ]

            Returns:
                str
        """
        try:
            domain_info = self.session.query(Domain).filter(Domain.domain_name == domain_name).first()
            delete_domain_conf_list = []
            for file in domain_files:
                delete_domain_conf_list.append(file["filePath"])
            domain_conf_to_delete = self.session.query(DomainConfInfo).filter(
                DomainConfInfo.domain_id == domain_info.domain_id).filter(
                DomainConfInfo.conf_path.in_(delete_domain_conf_list))
            domain_conf_to_delete.delete(synchronize_session=False)
            self.session.commit()
            return SUCCEED
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error("delete domain conf %s fail", domain_files)
            return DATABASE_DELETE_ERROR

    def get_domain_confs_by_domain(self, domain_name: str):
        """
            get domain conf from table

            Args:
                domain_name: test
            Returns:
                list
        """
        expected_conf_lists = {"domainName": domain_name, "confFiles": []}
        try:
            domain_info = self.session.query(Domain).filter(Domain.domain_name == domain_name).first()
            domain_conf_infos = self.session.query(DomainConfInfo).filter(
                DomainConfInfo.domain_id == domain_info.domain_id).all()
            for domain_conf in domain_conf_infos:
                conf = {"filePath": domain_conf.conf_path, "contents": domain_conf.conf_info}
                expected_conf_lists.get("confFiles").append(conf)

            return SUCCEED, expected_conf_lists
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error("query domain host fail")
            return DATABASE_QUERY_ERROR, expected_conf_lists
