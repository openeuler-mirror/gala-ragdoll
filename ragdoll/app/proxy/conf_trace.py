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
import ast
import datetime
import json
import math
import os
import uuid

import sqlalchemy
from sqlalchemy import desc, asc, func

from ragdoll.app import TARGETDIR, cache
from vulcanus import LOGGER
from vulcanus.restful.resp.state import SUCCEED, DATABASE_DELETE_ERROR, NO_DATA, UNKNOWN_ERROR, DATABASE_INSERT_ERROR, \
    DATABASE_QUERY_ERROR

from ragdoll.database import Domain, DomainHost, DomainConfInfo, HostConfSyncStatus, ConfTraceInfo
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

    def host_cancel(self, host_ids: list):
        """
        Delete host info in table and file

        Args:
            host_ids: host ids

        Returns:
            str
        """
        try:
            domain_names = dict()
            # 查询host_id属于哪个domain
            domain_host_query = (
                self.session.query(
                    DomainHost.host_id,
                    DomainHost.domain_id,
                    Domain.domain_name
                )
                .outerjoin(Domain, Domain.domain_id == DomainHost.domain_id)
                .filter(DomainHost.host_id.in_(host_ids))
            ).all()
            if len(domain_host_query) == 0:
                return NO_DATA
            for row in domain_host_query:
                domain_names[row.host_id] = row.domain_name

            # 删除/home/confTraceTest下的数据
            for host_id, domain_name in domain_names.items():
                domainPath = os.path.join(TARGETDIR, domain_name)
                hostPath = os.path.join(domainPath, "hostRecord.txt")
                if not os.path.isfile(hostPath) or (os.path.isfile(hostPath) and os.stat(hostPath).st_size == 0):
                    return NO_DATA
                with open(hostPath, 'r') as d_file:
                    lines = d_file.readlines()
                    with open(hostPath, 'w') as w_file:
                        for line in lines:
                            line_host_id = json.loads(str(ast.literal_eval(line)).replace("'", "\""))['host_id']
                            if host_id != line_host_id:
                                w_file.write(line)

            # 删除domain_host host_conf_sync_status
            self.session.query(DomainHost).filter(DomainHost.host_id.in_(host_ids)).delete(
                synchronize_session=False)
            self.session.query(HostConfSyncStatus).filter(HostConfSyncStatus.host_id.in_(host_ids)).delete(
                synchronize_session=False)
            self.session.commit()
            return SUCCEED
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error("delete hosts %s info fail", str(host_ids))
            self.session.rollback()
            return DATABASE_DELETE_ERROR
        except OSError as err:
            LOGGER.error("OS error: {0}".format(err))
            return UNKNOWN_ERROR

    def add_conf_trace_info(self, data):
        """
        add conf trace info to table

        Args:
            data: parameter, e.g.
                {
                    "domain_name": "aops",
                    "host_id": 1,
                    "conf_name": "/etc/hostname",
                    "info": ""
                }

        Returns:
            int: SUCCEED or DATABASE_INSERT_ERROR
        """
        try:
            domain_name = data.get('domain_name')
            host_id = data.get('host_id')
            conf_name = data.get('file')
            info = json.dumps(data)

            # 查询domain属于那个集群
            domain_info = self.session.query(Domain).filter(Domain.domain_name == domain_name).first()
            cluster_info = cache.clusters
            cluster_name = cluster_info.get(domain_info.cluster_id, {}).get("cluster_name")
            # 根据host_id 查询host_ip
            domain_host = self.session.query(DomainHost).filter(DomainHost.host_id == host_id).first()
            host_ip = domain_host.host_ip
            # 根据内容拼接配置变更信息
            info_str = f"用户:{data.get('user')} 进程:{data.get('cmd')} 修改了文件:{data.get('file')}"

            conf_trace_info = ConfTraceInfo(UUID=str(uuid.uuid4()), cluster_id=domain_info.cluster_id,
                                            cluster_name=cluster_name, domain_name=domain_name, host_id=host_id,
                                            host_ip=host_ip,
                                            conf_name=conf_name, info=info, conf_change_record=info_str,
                                            create_time=datetime.datetime.now())
            self.session.add(conf_trace_info)
            self.session.commit()
            LOGGER.info(
                f"add {conf_trace_info.domain_name} {conf_trace_info.host_id} {conf_trace_info.conf_name} conf trace "
                f"info succeed")
            return SUCCEED
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error(
                f"add {conf_trace_info.domain_name} {conf_trace_info.host_id} {conf_trace_info.conf_name} conf trace "
                f"info fail")
            self.session.rollback()
            return DATABASE_INSERT_ERROR

    def query_conf_trace_info(self, data):
        """
            query conf trace info from table

            Args:
                data: parameter, e.g.
                    {
                        "domain_name": "aops",
                        "host_id": 1,
                        "conf_name": "/etc/hostname",
                    }

            Returns:
                int: SUCCEED or DATABASE_INSERT_ERROR
        """
        result = {}
        try:
            result = self._sort_trace_info_by_column(data)
            self.session.commit()
            LOGGER.debug("query conf trace info succeed")
            return SUCCEED, result
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error("query conf trace info fail")
            return DATABASE_QUERY_ERROR, result

    def delete_conf_trace_info(self, data):
        """
            delete conf trace info from table

            Args:
                data: parameter, e.g.
                    {
                        "domain_name": "aops",
                        "host_ids": [1]
                    }

            Returns:
                int: SUCCEED or DATABASE_INSERT_ERROR
        """
        domainName = data['domain_name']
        host_ids = data['host_ids']
        try:
            # delete matched conf trace info
            if host_ids:
                conf_trace_filters = {ConfTraceInfo.host_id.in_(host_ids), ConfTraceInfo.domain_name == domainName}
            else:
                conf_trace_filters = {ConfTraceInfo.domain_name == domainName}
            confTraceInfos = self.session.query(ConfTraceInfo).filter(*conf_trace_filters).all()
            for confTraceInfo in confTraceInfos:
                self.session.delete(confTraceInfo)
            self.session.commit()
            return SUCCEED
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error("delete conf trace info fail")
            self.session.rollback()
            return DATABASE_DELETE_ERROR

    @staticmethod
    def _get_conf_trace_filters(data):
        """
        Generate filters

        Args:
            data(dict)

        Returns:
            set
        """
        domain_name = data.get('domain_name')
        host_id = data.get('host_id')
        conf_name = data.get('conf_name')
        filters = set()
        if domain_name:
            filters.add(ConfTraceInfo.domain_name == domain_name)
        if host_id:
            filters.add(ConfTraceInfo.host_id == host_id)
        if conf_name:
            filters.add(ConfTraceInfo.conf_name == conf_name)
        return filters

    @staticmethod
    def _get_conf_change_record_filters(data):
        """
        Generate filters

        Args:
            data(dict)

        Returns:
            set
        """
        domain_name = data.get('domain_name')
        host_ip = data.get('host_ip')
        conf_name = data.get('conf_name')
        filters = set()
        if domain_name:
            filters.add(ConfTraceInfo.domain_name == domain_name)
        if host_ip:
            filters.add(ConfTraceInfo.host_ip == host_ip)
        if conf_name:
            filters.add(ConfTraceInfo.conf_name == conf_name)
        return filters

    def _get_conf_trace_count(self, filters):
        """
        Sort conf trace info by specified column

        Args:
            filters(dict): sorted condition info

        Returns:
            int
        """
        total_count = self.session.query(func.count(ConfTraceInfo.UUID)).filter(*filters).scalar()
        return total_count

    def _sort_trace_info_by_column(self, data):
        """
        Sort conf trace info by specified column

        Args:
            data(dict): sorted condition info

        Returns:
            dict
        """
        result = {"total_count": 0, "total_page": 0, "conf_trace_infos": []}
        sort = data.get('sort')
        direction = desc if data.get('direction') == 'desc' else asc
        page = data.get('page')
        per_page = data.get('per_page')
        total_page = 1
        filters = self._get_conf_trace_filters(data)
        total_count = self._get_conf_trace_count(filters)
        if total_count == 0:
            return result

        if sort:
            if page and per_page:
                total_page = math.ceil(total_count / per_page)
                conf_trace_infos = (
                    self.session.query(ConfTraceInfo)
                    .filter(*filters)
                    .order_by(direction(getattr(ConfTraceInfo, sort)))
                    .offset((page - 1) * per_page)
                    .limit(per_page)
                    .all()
                )
            else:
                conf_trace_infos = self.session.query(ConfTraceInfo).filter(*filters).order_by(
                    direction(getattr(ConfTraceInfo, sort))).all()
        else:
            if page and per_page:
                total_page = math.ceil(total_count / per_page)
                conf_trace_infos = self.session.query(ConfTraceInfo).filter(*filters).offset(
                    (page - 1) * per_page).limit(per_page).all()
            else:
                conf_trace_infos = self.session.query(ConfTraceInfo).filter(*filters).all()

        LOGGER.error(f"conf_trace_infos is {conf_trace_infos}")
        for conf_trace_info in conf_trace_infos:
            info_dict = json.loads(conf_trace_info.info)
            info_str = f"用户:{info_dict.get('user')} 进程:{info_dict.get('cmd')} 修改了文件:{info_dict.get('file')}"
            ptrace_data = "=> ".join(f"{item['cmd']}:{item['pid']}" for item in info_dict.get('ptrace'))
            ptrace = f"{info_dict.get('cmd')} => {ptrace_data}"
            conf_trace_info = {
                "UUID": conf_trace_info.UUID,
                "domain_name": conf_trace_info.domain_name,
                "host_id": conf_trace_info.host_id,
                "conf_name": conf_trace_info.conf_name,
                "info": info_str,
                "create_time": str(conf_trace_info.create_time),
                "ptrace": ptrace
            }
            result["conf_trace_infos"].append(conf_trace_info)

        result["total_page"] = total_page
        result["total_count"] = total_count
        return result

    def find_conf_trace_info_day(self, data):
        """
            query conf trace info from table today

            Args:
                data: parameter, e.g.
                    {
                        "domain_name": "aops",
                        "host_id": 1,
                        "conf_name": "/etc/hostname",
                    }

            Returns:
                int: SUCCEED or DATABASE_INSERT_ERROR
        """
        result = []
        try:
            confTraceInfos = self.session.query(ConfTraceInfo).filter(
                ConfTraceInfo.domain_name == data.get('domain_name')) \
                .filter(ConfTraceInfo.host_id == data.get('host_id')) \
                .filter(func.DATE(ConfTraceInfo.create_time) == func.CURDATE()).all()
            LOGGER.debug("query today conf trace info succeed")
            return SUCCEED, confTraceInfos
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error("query today conf trace info fail")
            return DATABASE_QUERY_ERROR, result

    def _sort_conf_change_record_by_column(self, data):
        """
        Sort conf trace info by specified column

        Args:
            data(dict): sorted condition info

        Returns:
            dict
        """
        result = {"total_count": 0, "total_page": 0, "conf_change_records": []}
        sort = data.get('sort')
        direction = desc if data.get('direction') == 'desc' else asc
        page = data.get('page')
        per_page = data.get('per_page')
        total_page = 1
        filters = self._get_conf_change_record_filters(data)
        total_count = self._get_conf_trace_count(filters)
        if total_count == 0:
            return result

        if sort:
            if page and per_page:
                total_page = math.ceil(total_count / per_page)
                conf_change_records = (
                    self.session.query(ConfTraceInfo)
                    .filter(*filters)
                    .order_by(direction(getattr(ConfTraceInfo, sort)))
                    .offset((page - 1) * per_page)
                    .limit(per_page)
                    .all()
                )
            else:
                conf_change_records = self.session.query(ConfTraceInfo).filter(*filters).order_by(
                    direction(getattr(ConfTraceInfo, sort))).all()
        else:
            if page and per_page:
                total_page = math.ceil(total_count / per_page)
                conf_change_records = self.session.query(ConfTraceInfo).filter(*filters).offset(
                    (page - 1) * per_page).limit(per_page).all()
            else:
                conf_change_records = self.session.query(ConfTraceInfo).filter(*filters).all()
        for conf_trace_info in conf_change_records:
            conf_trace_info = {
                "UUID": conf_trace_info.UUID,
                "cluster_id": conf_trace_info.cluster_id,
                "cluster_name": conf_trace_info.cluster_name,
                "domain_name": conf_trace_info.domain_name,
                "host_id": conf_trace_info.host_id,
                "host_ip": conf_trace_info.host_ip,
                "conf_name": conf_trace_info.conf_name,
                "conf_change_record": conf_trace_info.conf_change_record,
                "create_time": str(conf_trace_info.create_time),
            }
            result["conf_change_records"].append(conf_trace_info)
        result["total_page"] = total_page
        result["total_count"] = total_count
        return result

    def query_conf_change_record(self, data):
        """
            query conf trace info from table

            Args:
                data: parameter, e.g.
                    {
                        "domain_name": "aops",
                        "host_id": 1,
                        "conf_name": "/etc/hostname",
                    }

            Returns:
                int: SUCCEED or DATABASE_INSERT_ERROR
        """
        result = {}
        try:
            result = self._sort_conf_change_record_by_column(data)
            self.session.commit()
            LOGGER.debug("query conf change record succeed")
            return SUCCEED, result
        except sqlalchemy.exc.SQLAlchemyError as error:
            LOGGER.error(error)
            LOGGER.error("query conf change record fail")
            return DATABASE_QUERY_ERROR, result
