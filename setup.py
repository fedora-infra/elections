#!/usr/bin/env python

"""
Setup script
"""

# These two lines are needed to run on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

from fedora_elections import __version__

from setuptools import setup

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
        'Flask-wtf', 'wtforms',
    ],
    test_suite="tests",
)
