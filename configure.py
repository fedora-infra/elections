#!/usr/bin/python -tt
# -*- coding: utf-8 -*-
#
# Copyright © 2013  Frank Chiulli <fchiulli@fedoraproject.org>
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2, or (at your option) any later version.  This
# program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the GNU
# General Public License along with this program; if not, write to the Free
# Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA. Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public License and
# may only be used or replicated with the express permission of Red Hat, Inc.
#
# Author(s):   Frank Chiulli <fchiulli@fedoraproject.org>
#

import glob
import os
import re

from optparse import OptionParser

#
# Process any command line options/switches.
#
parser = OptionParser()
parser.add_option('--install-conf', dest='confdir', action='store',
                  default='/etc',
                  help='Where to install configuration files.')
parser.add_option('--install-data', dest='datadir', action='store',
                  default='/usr/share',
                  help='Where to install data files.')
parser.add_option('--shared-state', dest='sharedstdir', action='store',
                  default='/var/lib',
                  help='Where to install shared state files.')

(options, args) = parser.parse_args()

confdir     = options.confdir
datadir     = options.datadir
sharedstdir = options.sharedstdir

print "  confdir     = %s" % confdir
print "  datadir     = %s" % datadir
print "  sharedstdir = %s" % sharedstdir

substs = {'@CONFDIR@':confdir,
          '@DATADIR@':datadir,
          '@SHAREDSTDIR@':sharedstdir
         }

pattern = re.compile("\.in$")

files = glob.glob('./*.in')

#
# Process all *.in files in the current directory.
#
if (files is not []):
    for orig_fn in files:
        if os.path.isfile(orig_fn):
            new_fn = re.sub(pattern, '', orig_fn)
            print "  Creating %s from %s" % (new_fn, orig_fn)
            fp1 = open(orig_fn, "r")
            file_contents = fp1.read()
            fp1.close()

            fp2 = open(new_fn, "w")
            for key, value in substs.iteritems():
                file_contents = file_contents.replace(key, value)
            fp2.write(file_contents)
            fp2.close()
