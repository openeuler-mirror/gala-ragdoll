#!/usr/bin/python3
"""
Description: setup up the A-ops manager service.
"""
import os
import platform
from setuptools import setup, find_packages
from setuptools.command.install import install


class CustomInstallCommand(install):
    """自定义安装命令，根据架构选择正确的脚本"""

    def run(self):
        # 根据架构选择源脚本
        arch = platform.machine()
        if arch == 'x86_64':
            source_script = 'ragdoll-filetrace-x86'
        elif arch in ['aarch64', 'arm64']:
            source_script = 'ragdoll-filetrace-aarch'
        else:
            raise ValueError(f"Unsupported architecture: {arch}")

        # 确保源脚本存在
        if not os.path.exists(source_script):
            raise FileNotFoundError(f"Source script '{source_script}' not found.")

        # 修改 data_files 中的条目，保持目标名称为 'ragdoll-filetrace'
        for i, (target_dir, files) in enumerate(self.distribution.data_files):
            if target_dir == '/usr/bin' and 'ragdoll-filetrace' in files:
                # 替换为实际的源脚本，但目标名称仍为 'ragdoll-filetrace'
                self.distribution.data_files[i] = (target_dir, [source_script])
                break

        # 执行默认安装
        install.run(self)


setup(
    name='ragdoll',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'libyang',
        'Flask',
        'Flask-RESTful',
        'requests',
        'SQLAlchemy',
        "redis",
        'gevent',
    ],
    data_files=[
        ('/etc/aops/conf.d', ['ragdoll.yml']),
        ('/etc/aops', ['ragdoll_crontab.yml']),
        ('/usr/lib/systemd/system', ["gala-ragdoll.service"]),
        ("/opt/aops/database", ["ragdoll/database/gala-ragdoll.sql"]),
        ("/usr/bin", ["ragdoll-filetrace"]),
        ("/usr/lib/systemd/system", ["ragdoll-filetrace.service"]),
    ],
    cmdclass={
        'install': CustomInstallCommand,
    },
    zip_safe=False,
)
