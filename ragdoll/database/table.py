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
@FileName: table.py
@Time: 2024/5/24 11:09
@Author: JiaoSiMao
Description:
"""
from sqlalchemy import Column
from sqlalchemy.sql.sqltypes import Integer, String

from vulcanus.database import Base


class Domain(Base):  # pylint: disable=R0903
    """
    Host table
    """

    __tablename__ = "domain"

    domain_id = Column(String(36), primary_key=True)
    domain_name = Column(String(50), nullable=False)
    priority = Column(Integer(), default=0)
    cluster_id = Column(String(36))


class DomainHost(Base):
    """
    Host group table
    """

    __tablename__ = "domain_host"

    host_id = Column(String(36), primary_key=True)
    domain_id = Column(String(36), primary_key=True)
    host_ip = Column(String(16), nullable=False)
    ipv6 = Column(String(10), nullable=False)


class DomainConfInfo(Base):
    """
    Host group table
    """

    __tablename__ = "domain_conf_info"

    domain_id = Column(String(36), primary_key=True)
    conf_path = Column(String(50), primary_key=True)
    conf_info = Column(String(), nullable=False)


class HostConfSyncStatus(Base):
    """
        Host conf sync status table
    """

    __tablename__ = "host_conf_sync_status"
    host_id = Column(String(36), primary_key=True)
    host_ip = Column(String(16), nullable=False)
    cluster_id = Column(String(36))
    domain_id = Column(String(36), primary_key=True)
    sync_status = Column(Integer(), default=0)
