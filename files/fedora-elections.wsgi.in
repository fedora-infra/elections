#-*- coding: UTF-8 -*-

# These two lines are needed to run on EL6
import __main__
__main__.__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

import sys
sys.stdout = sys.stderr

## Set the environment variable pointing to the configuration file
#import os
#os.environ['FEDORA_ELECTIONS_CONFIG'] = '/etc/fedora-elections/fedora-elections.cfg'

## The following is only needed if you did not install
## as a python module (for example if you run it from a git clone).
#sys.path.insert(0, '/path/to/fedora_elections/')

from fedora_elections import app as application
