# This file is part of fedmsg.
# Copyright (C) 2012 Red Hat, Inc.
#
# fedmsg is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# fedmsg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with fedmsg; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
# Authors:  Ralph Bean <rbean@redhat.com>
#
import socket
hostname = socket.gethostname()

config = dict(
    # This is a dict of possible addresses from which fedmsg can send
    # messages.  fedmsg.init(...) requires that a 'name' argument be passed
    # to it which corresponds with one of the keys in this dict.
    endpoints={
        # These are here so your local box can listen to the upstream
        # infrastructure's bus.  Cool, right?  :)
        "fedora-infrastructure": [
            "tcp://fedoraproject.org:9940",
            "tcp://stg.fedoraproject.org:9940",
        ],

        # This is the output side of the relay to which all other
        # services can listen.
        "relay_outbound": ["tcp://*:4001"],

        # And this is what our app actually uses.
        "fedora_elections.%s" % hostname: ["tcp://*:3007"],
    },

    relay_inbound="tcp://127.0.0.1:2003",
)
