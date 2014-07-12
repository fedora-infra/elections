#!/usr/bin/env python
import os
import __main__
__main__.__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

from fedora_elections import APP
from flask.ext.script import Manager, prompt_bool
from fedora_elections.models import create_tables

manager = Manager(APP)


@manager.command
def create_database():
    """Create database tables"""
    create_tables(APP.config['DB_URL'], debug=True)


@manager.command
def run_tests():
    """ Run application tests"""
    os.system('/bin/bash runtests.sh')


@manager.command
def deploy_apache():
    """ Deploy in apache"""
    if prompt_bool("I need sudo privileges for deploy the application, Run?"):
        os.system('sudo /bin/bash apache_deploy.sh')


@manager.command
def run():
    """Run application"""
    APP.debug = True
    APP.run()

if __name__ == '__main__':
    manager.run()
