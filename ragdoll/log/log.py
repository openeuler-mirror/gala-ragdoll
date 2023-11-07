#!/usr/bin/python3
# ******************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2021-2021. All rights reserved.
# licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# ******************************************************************************/
"""
Time:
Author:
Description: log module.
"""
import os
import stat
import logging

import configparser
from concurrent_log_handler import ConcurrentRotatingFileHandler

from ragdoll.const.conf_handler_const import CONFIG


class Logger:
    """
    Logger class.
    """

    def load_log_conf(self):
        """
        desc: get the log configuration
        """
        cf = configparser.ConfigParser()
        if os.path.exists(CONFIG):
            cf.read(CONFIG, encoding="utf-8")
        else:
            cf.read("config/gala-ragdoll.conf", encoding="utf-8")
        log_level = cf.get("log", "log_level")
        log_dir = cf.get("log", "log_dir")
        max_bytes = cf.get("log", "max_bytes")
        backup_count = cf.get("log", "backup_count")
        log_conf = {"log_level": log_level, "log_dir": log_dir, "max_bytes": int(max_bytes),
                    "backup_count": int(backup_count)}
        return log_conf

    def __init__(self):
        """
        Class instance initialization.
        """
        log_conf = self.load_log_conf()
        log_dir = log_conf.get("log_dir")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, mode=0o644)

        self.__log_name = os.path.join(log_dir, "ragdoll.log")
        self.__log_level = log_conf.get("log_level")
        self.__max_bytes = log_conf.get("max_bytes")
        self.__backup_count = log_conf.get("backup_count")
        self.__log_format = logging.Formatter(
            "%(asctime)s %(levelname)s %(module)s/%(funcName)s/%(lineno)s: %(message)s"
        )

        self.check()

    def check(self):
        """
        check whether parameter is valid.
        """
        self.__check_integer(self.__max_bytes, "max bytes")
        self.__check_integer(self.__backup_count, "backup count")

    @staticmethod
    def __check_integer(arg, comment):
        """
        check parameter of which type is int.

        Args:
            arg(int): parameter need to be checked.
            comment(str): decription.

        Raises:
            ValueError
        """
        if not isinstance(arg, int) or arg <= 0:
            raise ValueError("Invalid arg: %s: %r" % (comment, arg))

    def __create_logger(self):
        """
        create logger and set log level.

        Returns:
            logger
        """
        logger = logging.getLogger(__name__)
        logger.setLevel(self.__log_level)
        return logger

    def __console_logger(self):
        """
        create stream handler for logging to console.

        Returns:
            StreamHandler
        """
        # output log to the console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.__log_format)
        # console_handler.setLevel(level='DEBUG')

        return console_handler

    def __file_rotate_logger(self):
        """
        create rotated file handler for logging to file using size rotating.

        Returns:
            ConcurrentRotatingFileHandler
        """
        # log logrotate
        rotate_handler = ConcurrentRotatingFileHandler(
            filename=self.__log_name,
            mode="a",
            maxBytes=self.__max_bytes,
            backupCount=self.__backup_count,
            encoding="utf-8",
            chmod=(stat.S_IRUSR | stat.S_IWUSR),
        )
        rotate_handler.setFormatter(self.__log_format)

        return rotate_handler

    def get_logger(self):
        """
        get logger with handler.

        Returns:
            logger object
        """
        logger = self.__create_logger()

        logger.addHandler(self.__console_logger())
        logger.addHandler(self.__file_rotate_logger())

        return logger


LOGGER = Logger().get_logger()
