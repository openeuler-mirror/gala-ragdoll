# coding: utf-8

from setuptools import setup, find_packages

NAME = "ragdoll"
VERSION = "1.0.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = ["connexion"]

setup(
    name=NAME,
    version=VERSION,
    description="Configuration traceability",
    author_email="",
    url="https://gitee.com/openeuler/gala-ragdoll",
    keywords=["Swagger", "Configuration traceability"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['swagger/swagger.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['ragdoll=ragdoll.manage:main']},
    long_description="""\
    A
    """
)
