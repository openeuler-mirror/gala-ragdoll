import json
import os
from enum import Enum

from ragdoll.app.models.real_conf import RealConf
from ragdoll.app.models.real_conf_path import RealConfPath
from ragdoll.app.utils.format import Format
from ragdoll.app.utils.git_tools import GitTools

from vulcanus.log.log import LOGGER

PATH = "path"
EXCEPTED_VALUE = "expectedValue"
STRIKETHROUGH = '-'
KNOWN_ARCHITECTURES = [
    # Common architectures
    "x86_64",
    "i686",
    "aarch64"
]
STAT = "/usr/bin/stat"
LS = "/usr/bin/ls"
LL = "-l"
ACCESS = "Access"
UID = "Uid"
GID = "Gid"
TWOSPACE = "  "
SPACE = " "
Colon = ":"
FS = "/"
LeftParen = "("
RightParen = ")"
STRIKE = "-"
PERMISSION = 3
R = "r"
W = "w"
X = "x"
RPERM = 4
WPERM = 2
XPERM = 1
SPERM = 0

NOTFOUND = "NOT FOUND"
NOTSYNCHRONIZE = "NOT SYNCHRONIZE"
SYNCHRONIZED = "SYNCHRONIZED"


class SyncRes(Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class ConfTools(object):
    """
    desc: convert the configuration items controlled in the domain into dict storage
    """

    def __init__(self):
        self._managementConfs = []
        self._target_dir = "/home/confBak"

    @property
    def managementConfs(self):
        return self._managementConfs

    @managementConfs.setter
    def managementConfs(self, value):
        self._managementConfs = value

    @property
    def target_dir(self):
        return self._target_dir

    @target_dir.setter
    def target_dir(self, target_dir):
        self._target_dir = target_dir

    def listToDict(self, manaConfs):
        res = {}
        LOGGER.debug("manaConfs is : {}".format(manaConfs))
        for d_conf in manaConfs:
            path = d_conf.get(PATH)
            value = d_conf.get(EXCEPTED_VALUE).strip()
            level = path.split("/")
            d_res0 = {}
            d_res0[level[len(level) - 1]] = value

            returnObject = res
            returnCount = 0
            for count in range(0, len(level)):
                d_level = level[count]
                if returnObject.get(d_level):
                    returnObject = returnObject.get(d_level)
                else:
                    returnCount = count
                    break
            # to dict
            for count in range(len(level) - 2, returnCount, -1):
                d_res = {}
                key = level[count]
                d_res[key] = d_res0
                d_res0 = d_res

            # level less than 2
            if d_res0.get(level[returnCount]):
                returnObject[level[returnCount]] = d_res0.get(level[returnCount])
            else:
                returnObject[level[returnCount]] = d_res0

        return res

    def addFeatureInRealConf(self, realConfDict, featureList, domainName):
        """
        desc: Add feature information in the model to the actual configuration.
        """
        realConfWithFeature = {}
        LOGGER.debug("featureList is : {}".format(featureList))
        d_real_file = {}
        d_real_file[featureList[1]] = realConfDict
        d_real_feature = {}
        d_real_feature[featureList[0]] = d_real_file
        realConfWithFeature[domainName] = d_real_feature
        return realConfWithFeature

    def realConfToExpectDict(self, realConfResText):
        """
        desc: Convert the actual configuration into a dict of the same format as the expected
              configuration for easy comparison, using the model information.
         example:
            input:
                realConfResText: [
                                    {
                                        "confBaseInfos": [
                                            {
                                                "confContents": "{\"OS\": {\"baseurl\": \"http://repo.openeuler.org/openEuler-20.03-LTS-SP1/OS/$basearch/\", \"enabled\": \"1\", \"gpgcheck\": \"0\", \"gpgkey\": \"http://repo.openeuler.org/openEuler-20.03-LTS-SP1/OS/$basearch/RPM-GPG-KEY-openEuler\", \"name\": \"OS\"}}",
                                                "fileAttr": "0644",
                                                "fileOwner": "(root root)",
                                                "filePath": "/etc/yum.repos.d/openEuler.repo",
                                                "path": "yum/openEuler.repo/OS/name yum/openEuler.repo/OS/baseurl yum/openEuler.repo/enabled yum/openEuler.repo/gpgcheck yum/openEuler.repo/gpgkey",
                                                "rpmName": "openEuler-repos",
                                                "rpmRelease": "3.0.oe1.aarch64",
                                                "rpmVersion": "1.0"
                                            }
                                        ],
                                        "domainName": "OS",
                                        "hostID": "551d02da-7d8c-4357-b88d-15dc55ee22cc"
                                    }
                                ]
            output:
                res: [
                        {
                            "domainName":"OS",
                            "hostId": "551d02da-7d8c-4357-b88d-15dc55ee22cc",
                            "realConf": [
                                {
                                    "path": "OS/yum/openEuler.repo/OS/name"
                                    "realValue": "OS"
                                }
                                {
                                    "path": "OS/yum/openEuler.repo/OS/enabled"
                                    "realValue": "1"
                                },
                                .......
                            ]
                        }
                    ]
        """
        res = []
        LOGGER.debug("realConfResText is : {}".format(realConfResText))
        for d_conf in realConfResText:
            domainName = d_conf.get("domainName")
            hostId = d_conf.get("hostID")
            conf_base_infos = d_conf.get("confBaseInfos")
            real_conf = []
            if len(conf_base_infos) == 0:
                return None
            for d_conf_info in conf_base_infos:
                paths = d_conf_info.get("path").split(" ")
                confContents = json.loads(d_conf_info.get("confContents"))
                for d_path in paths:
                    x_path = os.path.join(domainName, d_path)
                    remove_feature_path = d_path.split("/")[2:]
                    d_path_value = confContents.copy()
                    for d_x_path in remove_feature_path:
                        if d_path_value.get(d_x_path):
                            d_path_value = d_path_value.get(d_x_path)
                    if type(d_path_value) == str:
                        d_real_conf = RealConf(path=x_path, real_value=d_path_value)
                        real_conf.append(d_real_conf)

            real_conf_path = RealConfPath(domain_name=domainName,
                                          host_id=hostId,
                                          real_conf=real_conf)
            res.append(real_conf_path)
        return res

    def compareManAndReal(self, real_conf, man_conf):
        """
        des: return a result of compare the manageConfs and realConfs.
             manageConfs is a result of http://0.0.0.0:11114/management/getManagementConf
             realConfs is a result of escaping through realConfToExpectDict interface after
                       calling http://0.0.0.0:11114/confs/queryRealConfs
        input:
            real_conf: {
                        "OS": {
                            "name": "OS",
                            "baseurl": "https://repo.huaweicloud.com/openeuler/openEuler-20.03-LTS-SP1/everything/x86_64/",
                            "enabled": "1",
                            "gpgcheck": "0",
                            "gpgkey": "http://repo.openeuler.org/openEuler-20.03-LTS-SP1/OS/$basearch/RPM-GPG-KEY-openEuler"
                        }
                        }
            man_conf: {
                        "OS": {
                            "name": "OS",
                            "baseurl": "https://repo.huaweicloud.com/openeuler/openEuler-20.03-LTS-SP1/everything/x86_64/",
                            "enabled": "1",
                            "gpgcheck": "0",
                            "gpgkey": "http://repo.openeuler.org/openEuler-20.03-LTS-SP1/OS/$basearch/RPM-GPG-KEY-openEuler"
                        }
                    }
        output: <SyncSta>
                string
        """

        dict1 = json.loads(real_conf)
        dict2 = json.loads(man_conf)

        res = ""
        for src_list, dst_list in zip(sorted(dict1), sorted(dict2)):
            if str(dict1[src_list]) != str(dict2[dst_list]):
                res = NOTSYNCHRONIZE
        if not res:
            res = SYNCHRONIZED

        return res

    def getRpmInfo(self, path):
        """
        desc: return the rpm_name\rpm_release\rpm_version for the package of path
        example:
            input: '/etc/yum.repos.d/openEuler.repo'
            output: openEuler-repos  1.0  3.0.oe1.aarch64
        """
        if not os.path.exists(path):
            return None
        cmd = "rpm -qf {}".format(path)
        gitTools = GitTools()
        package_string = gitTools.run_shell_return_output(cmd).decode()
        LOGGER.debug("package_string is : {}".format(package_string))
        if 'not owned by any package' in package_string:
            return None, None, None
        pkg, arch = Format.rsplit(package_string, Format.arch_sep(package_string))
        if arch not in KNOWN_ARCHITECTURES:
            pkg, arch = (package_string, None)
        pkg, release = Format.rsplit(pkg, '-')
        name, version = Format.rsplit(pkg, '-')
        # If the value of epoch needs to be returned separately,
        return name, release, version

    def getFileAttr(self, path):
        """
        desc: return the fileAtrr and fileOwner of path.
              if the /usr/bin/stat exists, we can use the case1:
                    command: /usr/bin/stat filename
                    output:
                        [root@openeuler-development-2-pafcm demo]# stat /etc/tcsd.conf
                        File: /etc/tcsd.conf
                        Size: 7046            Blocks: 16         IO Block: 4096   regular file
                        Device: fd00h/64768d    Inode: 262026      Links: 1
                        Access: (0600/-rw-------)  Uid: (   59/     tss)   Gid: (   59/     tss)
                        Context: system_u:object_r:etc_t:s0
                        Access: 2021-06-18 14:43:15.413173879 +0800
                        Modify: 2020-12-21 23:16:08.000000000 +0800
                        Change: 2021-01-13 16:50:31.257896622 +0800
                        Birth: 2021-01-13 16:50:31.257896622 +0800
              else, we use the case2:
                    command: ls -l filename
                    output:
                        [root@openeuler-development-2-pafcm demo]# ls -l /etc/tcsd.conf
                        -rw-------. 1 tss tss 6.9K Dec 21 23:16 /etc/tcsd.conf

        example:
            input: '/etc/yum.repos.d/openEuler.repo'
            output: 0644 (root root)
        """
        if not os.path.exists(STAT):
            fileAttr, fileOwner = self.getFileAttrByLl(path)
            return fileAttr, fileOwner

        cmd = STAT + SPACE + path
        gitTools = GitTools()
        stat_rest = gitTools.run_shell_return_output(cmd).decode()
        LOGGER.debug("the stat_rest is : {}".format(stat_rest))
        fileAttr = ""
        fileOwner = ""
        lines = stat_rest.splitlines()
        for line in lines:
            if ACCESS in line and UID in line and GID in line:
                d_lines = line.split(RightParen + TWOSPACE)
                for d_line in d_lines:
                    d_line = d_line.lstrip()
                    if d_line.startswith(ACCESS):
                        fileAttr = d_line.split(FS)[0].split(LeftParen)[1]
                    elif d_line.startswith(UID):
                        fileUid = d_line.split(LeftParen)[1].split(FS)[1].lstrip()
                    elif d_line.startswith(GID):
                        fileGid = d_line.split(LeftParen)[1].split(FS)[1].lstrip().split(RightParen)[0]
                    else:
                        continue
                fileOwner = LeftParen + fileUid + SPACE + fileGid + RightParen

        if not fileAttr or not fileOwner:
            fileAttr, fileOwner = self.getFileAttrByLL(path)
        LOGGER.debug("fileAttr is : {}".format(fileAttr))
        LOGGER.debug("fileOwner is : {}".format(fileOwner))
        return fileAttr, fileOwner

    def getFileAttrByLL(self, path):
        """
        desc: we can use the command 'ls -l filename' to get the Attribute information of the path.
        example:
            command: ls -l filename
            commandOutput:
                [root@openeuler-development-2-pafcm demo]# ls -l /etc/tcsd.conf
                -rw-------. 1 tss tss 6.9K Dec 21 23:16 /etc/tcsd.conf
        calculate score:
                the first digit indicates the type: [d]->directory, [-]->files
                then every 3 are grouped, indicates read/write/execute
                score: r->4 w->2 x->1
        """
        if not os.path.exists(LS):
            return None, None
        cmd = LS + SPACE + LL + SPACE + path
        LOGGER.debug("cmd is : {}".format(cmd))
        gitTools = GitTools()
        ll_res = gitTools.run_shell_return_output(cmd).decode()
        LOGGER.debug("ll_res is : {}".format(ll_res))
        ll_res_list = ll_res.split(SPACE)

        fileType = ll_res_list[0]
        permssions = "0"
        for perm in range(0, PERMISSION):
            items = fileType[1 + perm * PERMISSION: (perm + 1) * PERMISSION + 1]
            value = 0
            for d_item in items:
                d_item_value = self.switch_perm(d_item)
                value = value + d_item_value
            permssions = permssions + str(value)
        LOGGER.debug("the perssion is : {}".format(permssions))

        fileOwner = LeftParen + ll_res_list[2] + SPACE + ll_res_list[3] + RightParen
        LOGGER.debug("the fileOwner is : {}".format(fileOwner))

        return permssions, fileOwner

    def switch_perm(self, permValue):
        if permValue == R:
            return RPERM
        elif permValue == W:
            return WPERM
        elif permValue == X:
            return XPERM
        else:
            return SPERM

    def getXpathInManagerConfs(self, manageConfs):
        """
        desc: generate the xpath list of configuration items.
        """
        confXpath = []
        for d_conf in manageConfs:
            path = d_conf.get('path')
            confXpath.append(path)

        return confXpath

    def writeBakFileInPath(self, path, content):
        """
        desc: Create the Path file, and write the content content, return the write result
        """
        res = False
        cwd = os.getcwd()
        os.umask(0o077)
        if not os.path.exists(self._target_dir):
            os.mkdir(self._target_dir)

        os.chdir(self._target_dir)
        path_git = Format.two_abs_join(self.target_dir, path)
        paths = path_git.split('/')
        path_git_delete_last = ""
        for d_index in range(0, len(paths) - 1):
            path_git_delete_last = path_git_delete_last + '/' + paths[d_index]
        if not os.path.exists(path_git):
            cmd = "mkdir -p " + path_git_delete_last
            LOGGER.debug("cmd is : {}".format(cmd))
            gitTools = GitTools()
            ll_res = gitTools.run_shell_return_output(cmd).decode()

        if not os.path.exists(path_git_delete_last):
            return res

        with open(path_git, 'w') as d_file:
            d_file.write(content)
            res = True
        os.chdir(cwd)

        return res

    def getRealConfByPath(self, real_conf, path):
        """
        desc: Returns the index and true value corresponding to the PATH in real_conf
        exmaple:
            input:
                real_conf: [
                    {
                        'path': 'OS/yum/openEuler.repo/OS/name',
                        'real_value': 'OS'
                    },
                    {
                        'path': 'OS/yum/openEuler.repo/OS/baseurl',
                        'real_value': 'http://repo.openeuler.org/openEuler-20.03-LTS-SP1/OS/$basearch/'
                    }]
                path: 'OS/yum/openEuler.repo/OS/name'
            output:
                index: 0
                value: 'OS'
        """
        index = 0
        value = ""
        for count in range(0, len(real_conf)):
            d_real = real_conf[count]
            if d_real.path == path:
                index = count
                value = d_real.real_value.strip()
                break

        return index, value

    def getExpConfByPath(self, manage_confs, path):
        """
        desc: Returns the index and true value corresponding to the PATH in real_conf
        exmaple:
            input:
                manage_confs: [
                    {
                        'path': 'OS/yum/openEuler.repo/OS/name',
                        'expectedValue': 'OS'
                    },
                    {
                        'path': 'OS/yum/openEuler.repo/OS/baseurl',
                        'expectedValue': 'http://repo.openeuler.org/openEuler-20.03-LTS-SP1/OS/$basearch/'
                    }]
                path: 'OS/yum/openEuler.repo/OS/name'
            output:
                index: 0
                value: 'OS'
        """
        index = 0
        value = ""
        for count in range(0, len(manage_confs)):
            d_man = manage_confs[count]
            if d_man.get('path') == path:
                index = count
                value = d_man.get('expectedValue')
                break

        return index, value

    def realConfToConfContents(self, realConf):
        """
        desc: Converts real_conf to contents in realConfInfo
        params:
            input:
                realConf: the type of RealConfPath
            output:
                confContents: The return value of the /confs/QueryRealconfs interface, the type is confContents in RealconfBaseInfo
        example:
            realConf:[
                        {
                            "path": "OS/yum/openEuler.repo/OS/name",
                            "real_value": "OS"
                        },
                        {
                            "path": "OS/yum/openEuler.repo/OS/baseurl",
                            "real_value": "https://repo.huaweicloud.com/openeuler/openEuler-20.03-LTS-SP1/everything/x86_64/"
                        }]
            confContents:"{
                            "OS": {
                                "baseurl": "http://repo.openeuler.org/openEuler-20.03-LTS-SP1/OS/$basearch/",
                                "name": "OS"
                            }
                        }"

        """
        # Path format: domain/feature/conf
        STARTINDEX = 3
        res_string = ""
        res = {}
        for d_conf in realConf:
            path = d_conf.path
            value = d_conf.real_value.strip()
            level = path.split("/")
            d_res0 = {}
            d_res0[level[len(level) - 1]] = value

            returnObject = res
            returnCount = 0
            for count in range(STARTINDEX, len(level)):
                d_level = level[count]
                if returnObject.get(d_level):
                    returnObject = returnObject.get(d_level)
                else:
                    returnCount = count
                    break
            # to dict
            for count in range(len(level) - 2, returnCount, -1):
                d_res = {}
                key = level[count]
                d_res[key] = d_res0
                d_res0 = d_res
            # level less than 2
            if d_res0.get(level[returnCount]):
                returnObject[level[returnCount]] = d_res0.get(level[returnCount])
            else:
                returnObject[level[returnCount]] = d_res0
        res_string = json.dumps(res)
        return res_string

    def syncConf(self, contents, path):
        """
        desc:  Put the new configuration into the environment with the path.
        return: the result of effective
        example:
            input:
                contents: [
                    '[OS]',
                    'name=OS',
                    'baseurl=https://repo.huaweicloud.com/openeuler/openEuler-20.03-LTS-SP1/everything/x86_64/',
                    'enabled=1',
                    'gpgcheck=0',
                    'gpgkey=http://repo.openeuler.org/openEuler-20.03-LTS-SP1/OS/$basearch/RPM-GPG-KEY-openEuler'
                ]
                path: '/etc/yum.repos.d/openEuler.repo'
            output:
                res : true or false
        """
        res = 0
        res = Format.set_file_content_by_path(contents, path)
        return res

    def wirteFileInPath(self, path, content):
        """
        desc: Create the Path file, and write the content content, return the write result
        """
        res = False
        path_delete_last = ""
        os.umask(0o077)
        if not os.path.exists(path):
            paths = path.split('/')
            for d_index in range(0, len(paths) - 1):
                path_delete_last = path_delete_last + '/' + paths[d_index]
            if not os.path.exists(path_delete_last):
                cmd = "mkdir -p " + path_delete_last
                LOGGER.debug("cmd is : {}".format(cmd))
                gitTools = GitTools()
                ll_res = gitTools.run_shell_return_output(cmd).decode()
            LOGGER.debug("path_delete_last IS :{}".format(path_delete_last))
            if not os.path.exists(path_delete_last):
                return res

        with open(path, 'w') as d_file:
            d_file.writelines(content)
            res = True

        return res
