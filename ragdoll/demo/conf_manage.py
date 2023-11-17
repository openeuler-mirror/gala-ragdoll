import requests
import json

from ragdoll.log.log import LOGGER
from ragdoll.models.domain_name import DomainName
from ragdoll.models.conf import Conf
from ragdoll.models.confs import Confs
from ragdoll.models.manage_conf import ManageConf
from ragdoll.models.manage_confs import ManageConfs
from ragdoll.demo.conf import server_port
from ragdoll.encoder import JSONEncoder


class ConfManage(object):
    def conf_add(self, args):
        domain_name = args.domain_name
        file_path_list = args.file_path
        contents_list = args.contents
        host_id_list = args.host_id
        if not domain_name or not file_path_list:
            LOGGER.error("ERROR: Input error for conf_add!\n")
            return
        
        conf_file = []
        if (contents_list and (len(file_path_list) == len(contents_list))):
            for i in range(len(file_path_list)):
                conf = Conf(file_path=file_path_list[i], contents=contents_list[i])
                conf_file.append(conf)
        elif (host_id_list and (len(file_path_list) == len(host_id_list))):
            for i in range(len(file_path_list)):
                conf = Conf(file_path=file_path_list[i], host_id=host_id_list[i])
                conf_file.append(conf)
        else:
            LOGGER.error("ERROR: Input error as invlid param!\n")
            return

        data = Confs(domain_name=domain_name, conf_files=conf_file)
        url = "http://0.0.0.0:{}/management/addManagementConf".format(server_port)
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(data, cls=JSONEncoder), headers=headers)
        
        LOGGER.debug(json.loads(response.text).get("msg"))
        return

    def conf_query(self, args):
        domain_name = args.domain_name
        if not domain_name:
            LOGGER.error("ERROR: Input error for conf_query!\n")
            return

        data = DomainName(domain_name=domain_name)
        url = "http://0.0.0.0:{}/management/getManagementConf".format(server_port)
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(data, cls=JSONEncoder), headers=headers)
        
        if response.status_code != 200:
            LOGGER.warning(json.loads(response.text).get("msg"))
        else:
            LOGGER.debug("The managed configurations in the domain[{}] is:{}".format(domain_name, json.loads(response.text).get("confFiles")))
        return

    def conf_delete(self, args):
        domain_name = args.domain_name
        file_path_list = args.file_path
        if not domain_name or not file_path_list:
            LOGGER.error("ERROR: Input error for conf_delete!\n")
            return
        
        conf_files = []
        for file_path in file_path_list:
            conf = ManageConf(file_path=file_path)
            conf_files.append(conf)
        
        data = ManageConfs(domain_name=domain_name, conf_files=conf_files)
        url = "http://0.0.0.0:{}/management/deleteManagementConf".format(server_port)
        headers = {"Content-Type": "application/json"}
        response = requests.delete(url, data=json.dumps(data, cls=JSONEncoder), headers=headers)
        
        if response.status_code != 200:
            LOGGER.warning("Fail to delete {} in {}.".format(file_path_list, domain_name))
        else:
            LOGGER.debug(json.loads(response.text).get("msg"))
        return

    def conf_changelog(self, args):
        domain_name = args.domain_name
        file_path_list = args.file_path
        if not domain_name or not file_path_list:
            LOGGER.error("ERROR: Input error for conf_changelog!\n")
            return
        
        conf_files = []
        for file_path in file_path_list:
            conf = ManageConf(file_path=file_path)
            conf_files.append(conf)
        
        data = ManageConfs(domain_name=domain_name, conf_files=conf_files)
        url = "http://0.0.0.0:{}/management/queryManageConfChange".format(server_port)
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, data=json.dumps(data, cls=JSONEncoder), headers=headers)
        
        if not json.loads(response.text).get("confBaseInfos"):
            LOGGER.warning(json.loads(response.text).get("msg"))
        else:
            changelog = []
            for i in json.loads(response.text).get("confBaseInfos"):
                changelog.append(i)
            LOGGER.debug("The changelog of domain [{}] is:{}".format(domain_name, changelog))
        return


