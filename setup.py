#!/usr/bin/env python

"""
Setup script
"""

import os
import re
from setuptools import setup

versionfile = os.path.join(
    os.path.dirname(__file__), 'fedora_elections', '__init__.py')

# Thanks to SQLAlchemy:
# https://github.com/zzzeek/sqlalchemy/blob/master/setup.py#L104
with open(versionfile) as stream:
    __version__ = re.compile(
        r".*__version__ = '(.*?)'", re.S
    ).match(stream.read()).group(1)

setup(
    name='fedora-elections',
    version=__version__,
    author='Frank Chiulli',
    author_email='fchiulli@fedoraproject.org',
    packages=['fedora_elections'],
    include_package_data=True,
    install_requires=[
        'Flask', 'SQLAlchemy>=0.7', 'python-fedora', 'kitchen',
        'python-openid', 'python-openid-teams', 'python-openid-cla',
        'Flask-wtf', 'wtforms', 'fedora-elections-messages',
    ],
    test_suite="tests",
)
