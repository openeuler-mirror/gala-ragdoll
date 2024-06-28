#!/usr/bin/python3
"""
Description: setup up the A-ops manager service.
"""

from setuptools import setup, find_packages

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
    ],
    zip_safe=False,
)
