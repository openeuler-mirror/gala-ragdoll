# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from ragdoll.models.base_model_ import Model
from ragdoll import util
from ragdoll.models.single_config import SingleConfig


class ConfIsSynced(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, file_path: str = None, is_synced: str = None,
                 single_conf: List[SingleConfig] = None):  # noqa: E501
        """ConfIsSynced - a model defined in Swagger

        :param file_path: The xpath of this configuration item.  # noqa: E501
        :type file_path: str
        :param is_synced: The sync_status of this configuration item.  # noqa: E501
        :type is_synced: str
        """
        self.swagger_types = {
            'file_path': str,
            'is_synced': str,
            'single_conf': List[SingleConfig]
        }

        self.attribute_map = {
            'file_path': 'file_path',
            'is_synced': 'isSynced',
            'single_conf': 'singleConf'
        }

        self._path = file_path
        self._is_synced = is_synced
        self._single_conf = single_conf

    @classmethod
    def from_dict(cls, dikt) -> 'ConfIsSynced':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ConfIsSynced of this Host.  # noqa: E501
        :rtype: ConfIsSynced
        """
        return util.deserialize_model(dikt, cls)

    @property
    def file_path(self) -> str:
        """Gets the file_path of this configuration item.

        file_path  # noqa: E501

        :return: The Xpath of this configuration item.
        :rtype: str
        """
        return self._path

    @file_path.setter
    def file_path(self, file_path: str):
        """Sets the Xpath of this configuration item.

        domain name  # noqa: E501

        :param file_path: The Xpath of this configuration item.
        :type file_path: str
        """

        self._path = file_path

    @property
    def is_synced(self) -> str:
        """Gets the status of synced of this configuration item.

        :return: the status of synced of this configuration item.
        :rtype: str
        """
        return self._is_synced

    @is_synced.setter
    def is_synced(self, is_synced: str):
        """Sets the is_synced of this configuration item.


        :param is_synced: The is_synced of this configuration item.
        :type is_synced: str
        """
        allowed_values = ["NOT FOUND", "NOT SYNCHRONIZE", "SYNCHRONIZED"]  # noqa: E501
        if is_synced not in allowed_values:
            raise ValueError(
                "Invalid value for `is_synced` ({0}), must be one of {1}"
                .format(is_synced, allowed_values)
            )

        self._is_synced = is_synced

    @property
    def single_conf(self) -> List[SingleConfig]:
        """Gets the single_conf of this ConfIsSynced.


        :return: The single_conf of this ConfIsSynced.
        :rtype: List[SingleConfig]
        """
        return self._single_conf

    @single_conf.setter
    def single_conf(self, single_conf: List[SingleConfig]):
        """Sets the single_conf of this ConfIsSynced.


        :param single_conf: the single_conf of this ConfIsSynced.
        :type single_conf: List[SingleConfig]
        """

        self._single_conf = single_conf
