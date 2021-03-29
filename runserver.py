#!/usr/bin/env python2

# These two lines are needed to run on EL6
__requires__ = ['SQLAlchemy >= 0.8', 'jinja2 >= 2.4']
import pkg_resources

import argparse
import sys
import os


parser = argparse.ArgumentParser(
    description='Run the Fedora election app')
parser.add_argument(
    '--config', '-c', dest='config',
    help='Configuration file to use for packages.')
parser.add_argument(
    '--debug', dest='debug', action='store_true',
    default=False,
    help='Expand the level of data returned.')
parser.add_argument(
    '--profile', dest='profile', action='store_true',
    default=False,
    help='Profile the application.')
parser.add_argument(
    '--port', '-p', default=5005,
    help='Port for the flask application.')
parser.add_argument(
    '--cert', '-s', default=None,
    help='Filename of SSL cert for the flask application.')
parser.add_argument(
    '--key', '-k', default=None,
    help='Filename of the SSL key for the flask application.')
parser.add_argument(
    '--host', default="127.0.0.1",
    help='Hostname to listen on. When set to 0.0.0.0 the server is available \
    externally. Defaults to 127.0.0.1 making the it only visable on localhost')

args = parser.parse_args()

from fedora_elections import APP

if args.profile:
    from werkzeug.contrib.profiler import ProfilerMiddleware
    APP.config['PROFILE'] = True
    APP.wsgi_app = ProfilerMiddleware(APP.wsgi_app, restrictions=[30])

if args.config:
    config = args.config
    if not config.startswith('/'):
        here = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        config = os.path.join(here, config)
    os.environ['FEDORA_ELECTIONS_CONFIG'] = config

APP.debug = True
if args.cert and args.key:
    APP.run(host=args.host, port=int(args.port), ssl_context=(args.cert, args.key))
else:
    APP.run(host=args.host, port=int(args.port))
