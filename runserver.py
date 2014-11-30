#!/usr/bin/env python
import __main__
__main__.__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

import sys
from werkzeug.contrib.profiler import ProfilerMiddleware

from fedora_elections import APP
APP.debug = True

if '--profile' in sys.argv:
    APP.config['PROFILE'] = True
    APP.wsgi_app = ProfilerMiddleware(APP.wsgi_app, restrictions=[30])

APP.run()
