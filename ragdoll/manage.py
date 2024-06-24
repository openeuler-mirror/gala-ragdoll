#!/usr/bin/python3
try:
    from gevent import monkey, pywsgi

    monkey.patch_all(ssl=False)
except:
    pass

from vulcanus.manage import init_application
from ragdoll.conf import configuration
from ragdoll.url import URLS
from ragdoll.utils.prepare import Prepare
from ragdoll.utils.yang_module import YangModule


def load_prepare():
    git_dir = configuration.git.get("GIT_DIR").replace("\"", "")
    git_user_name = configuration.git.get("USER_NAME").replace("\"", "")
    git_user_email = configuration.git.get("USER_EMAIL").replace("\"", "")

    prepare = Prepare(git_dir)
    prepare.mkdir_git_warehose(git_user_name, git_user_email)


def load_yang():
    yang_modules = YangModule()


def main():
    _app = init_application(name="ragdoll", settings=configuration, register_urls=URLS)
    # prepare to load config
    load_prepare()
    # load yang modules
    load_yang()
    print("configuration.ragdoll.get('ip') is ", configuration.ragdoll.get('IP'))
    return _app


app = main()

if __name__ == "__main__":
    app.run(host=configuration.ragdoll.get('IP'), port=configuration.ragdoll.get("PORT"))
