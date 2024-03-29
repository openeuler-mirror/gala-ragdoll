import requests
import json

from ragdoll.log.log import LOGGER
from ragdoll.models.domain_name import DomainName
from ragdoll.models.conf_host import ConfHost
from ragdoll.demo.conf import server_port
from ragdoll.encoder import JSONEncoder


class ConfSync(object):
    def sync_conf(self, args):
        domain_name = args.domain_name
        host_id_list = args.host_id
        if not domain_name or not host_id_list:
            LOGGER.error("ERROR: Input error for sync_conf!\n")
            return

        host_ids = []
        for i in host_id_list:
            host_id = {"hostId": i}
            host_ids.append(host_id)
        
        data = ConfHost(domain_name=domain_name, host_ids=host_ids)
        url = "http://0.0.0.0:{}/confs/syncConf".format(server_port)
        headers = {"Content-Type": "application/json"}
        response = requests.put(url, data=json.dumps(data, cls=JSONEncoder), headers=headers)
        
        if response.status_code != 200:
            LOGGER.error(json.loads(response.text))
        return

    def sync_status(self, args):
        domain_name = args.domain_name
        if not domain_name:
            LOGGER.error("ERROR: Input error for sync_status!\n")
            return
        
        data = DomainName(domain_name=domain_name)
        url = "http://0.0.0.0:{}/confs/getDomainStatus".format(server_port)
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(data, cls=JSONEncoder), headers=headers)
        
        if response.status_code != 200:
            LOGGER.warning(json.loads(response.text).get("msg"))
        else:
            LOGGER.debug(json.loads(response.text))
        return

    def query_real_conf(self, args):
        domain_name = args.domain_name
        host_id_list = args.host_id
        if not domain_name or not host_id_list:
            LOGGER.error("ERROR: Input error for query_real_conf!\n")
            return
        
        host_ids = []
        for i in host_id_list:
            host_id = {"hostId": i}
            host_ids.append(host_id)
        
        data = ConfHost(domain_name=domain_name, host_ids=host_ids)
        url = "http://0.0.0.0:{}/confs/queryRealConfs".format(server_port)
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(data, cls=JSONEncoder), headers=headers)

        if response.status_code != 200:
            LOGGER.warning(json.loads(response.text).get("msg"))
        else:
            LOGGER.debug(json.loads(response.text))
        return

    def query_expected_conf(self, args):
        if not args:
            return
        url = "http://0.0.0.0:{}/confs/queryExpectedConfs".format(server_port)
        response = requests.post(url)
        LOGGER.debug(json.loads(response.text))
        return
