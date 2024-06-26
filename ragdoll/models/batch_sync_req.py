# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from ragdoll.models.base_model_ import Model
from ragdoll import util
from ragdoll.models.sync_host_confs import SyncHostConfs


class BatchSyncReq(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, domain_name: str = None, host_ids: List[int] = None):  # noqa: E501

        """ConfHost - a model defined in Swagger

        :param domain_name: The domain_name of this BatchSyncReq.  # noqa: E501
        :type domain_name: str
        :param host_ids: The host_ids of this BatchSyncReq.  # noqa: E501
        :type host_ids: List[int]
        """
        self.swagger_types = {
            'domain_name': str,
            'host_ids': List[int]
        }

        self.attribute_map = {
            'domain_name': 'domainName',
            'host_ids': 'hostIds'
        }

        self._domain_name = domain_name
        self._host_ids = host_ids

    @classmethod
    def from_dict(cls, dikt) -> 'BatchSyncReq':
        """Returns the dict as a model

       :param dikt: A dict.
       :type: dict
       :return: The BatchSyncReq of this BatchSyncReq.  # noqa: E501
       :rtype: BatchSyncReq
       """
        return util.deserialize_model(dikt, cls)

    @property
    def domain_name(self) -> str:
        """Gets the domain_name of this BatchSyncReq.

       domain name  # noqa: E501

       :return: The domain_name of this BatchSyncReq.
       :rtype: str
       """
        return self._domain_name

    @domain_name.setter
    def domain_name(self, domain_name: str):
        """Sets the domain_name of this BatchSyncReq.

       domain name  # noqa: E501

       :param domain_name: The domain_name of this BatchSyncReq.
       :type domain_name: str
       """

        self._domain_name = domain_name

    @property
    def host_ids(self) -> List[int]:
        """Gets the host_ids of this BatchSyncReq.


        :return: The host_ids of this BatchSyncReq.
        :rtype: List[int]
        """

        return self._host_ids

    @host_ids.setter
    def host_ids(self, host_ids: List[int]):
        """Sets the sync_list of this BatchSyncReq.


        :param host_ids: The host_ids of this BatchSyncReq.
        :type host_ids: List[int]
        """

        self._host_ids = host_ids
