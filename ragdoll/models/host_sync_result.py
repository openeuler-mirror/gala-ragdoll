# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from ragdoll.models.base_model_ import Model
from ragdoll.models.conf_synced_res import ConfSyncedRes

from ragdoll import util


class HostSyncResult(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, host_id: str=None, sync_result: List[ConfSyncedRes]=None):  # noqa: E501
        """HostSyncResult - a model defined in Swagger

        :param host_id: The host_id of this HostSyncResult.  # noqa: E501
        :type host_id: str
        :param sync_result: The sync_result of this HostSyncResult.  # noqa: E501
        :type sync_result: List[ConfSyncedRes]
        """
        self.swagger_types = {
            'host_id': str,
            'sync_result': List[ConfSyncedRes]
        }

        self.attribute_map = {
            'host_id': 'hostId',
            'sync_result': 'syncResult'
        }

        self._host_id = host_id
        self._sync_result = sync_result

    @classmethod
    def from_dict(cls, dikt) -> 'HostSyncResult':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The HostSyncResult of this HostSyncResult.  # noqa: E501
        :rtype: HostSyncResult
        """
        return util.deserialize_model(dikt, cls)

    @property
    def host_id(self) -> str:
        """Gets the host_id of this HostSyncResult.

        the id of host  # noqa: E501

        :return: The host_id of this HostSyncResult.
        :rtype: str
        """
        return self._host_id

    @host_id.setter
    def host_id(self, host_id: str):
        """Sets the host_id of this HostSyncResult.

        the id of host  # noqa: E501

        :param host_id: The host_id of this HostSyncResult.
        :type host_id: str
        """

        self._host_id = host_id

    @property
    def sync_result(self) -> List[ConfSyncedRes]:
        """Gets the sync_result of this HostSyncResult.


        :return: The sync_result of this HostSyncResult.
        :rtype: List[ConfSyncedRes]
        """
        return self._sync_result

    @sync_result.setter
    def sync_result(self, sync_result: List[ConfSyncedRes]):
        """Sets the sync_result of this HostSyncResult.


        :param sync_result: The sync_result of this HostSyncResult.
        :type sync_result: List[ConfSyncedRes]
        """

        self._sync_result = sync_result
