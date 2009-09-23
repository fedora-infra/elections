#!/usr/bin/python
__requires__ = 'elections'

import sys
sys.path.append('/usr/share/elections/elections')
sys.path.append('/usr/share/elections')
sys.stdout = sys.stderr

import pkg_resources
pkg_resources.require('CherryPy <= 3.0alpha')

import os
#os.environ['PYTHON_EGG_CACHE'] = '/srv/elections/elections.eggcache/'

import atexit
import cherrypy
import cherrypy._cpwsgi
import turbogears
from turbogears import startup
from fedora.tg.util import enable_csrf

turbogears.update_config(configfile="/etc/elections.cfg", modulename="elections.config")

startup.call_on_startup.append(enable_csrf)

import elections.controllers

cherrypy.root = elections.controllers.Root()

if cherrypy.server.state == 0:
    atexit.register(cherrypy.server.stop)
    cherrypy.server.start(init_only=True, server_class=None)

def application(environ, start_response):
    environ['SCRIPT_NAME'] = ''
    return cherrypy._cpwsgi.wsgiApp(environ, start_response)
