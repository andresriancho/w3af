# -*- coding: iso-8859-1 -*-

"""Scanning tasks.

@var default_scantime: Time to spend probing the target expressed in seconds.
@type default_scantime: C{int}

@var default_parallelism: Number of parallel threads to launch for the scan.
@type default_parallelism: C{int}

@var default_conf_dir: Path to the directory where the configuration file is
located.
@type default_conf_dir: C{str}

@var default_conf_file: Name of the default configuration file for halberd.
@type default_conf_file: C{str}

@var default_ratio_threshold: Minimum clues-to-realservers ratio to trigger a
clue reanalysis.
@type default_ratio_threshold: C{float}

@var default_out: Default place where to write reports (None means stdout).
@type default_out: C{str}
"""

# Copyright (C) 2004, 2005, 2006 Juan M. Bello Rivas <jmbr@superadditive.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import os

import Halberd.conflib


default_scantime = 15

default_parallelism = 4

default_conf_dir = os.path.join(os.path.expanduser('~'), '.halberd')
default_conf_file = os.path.join(default_conf_dir,
                                 'halberd' + os.extsep + 'cfg')

default_ratio_threshold = 0.6

default_out = None


class ConfError(Exception):
    """Error with configuration file(s)
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


class ScanTask:
    """Describes the way a scan should be performed.

    @ivar verbose: Display status information during the scan.
    @type verbose: C{bool}

    @ivar debug: Display debug information.
    @type debug: C{bool}

    @ivar urlfile: Root folder to use for storing results of MultiScans.
    @type urlfile: C{str}

    @ivar url: URL to scan.
    @type url: C{str}

    @ivar addr: Address of the target web server.
    @type addr: C{str}

    @ivar proxy_serv_addr: Address + port where to listen when operating as a
    proxy.
    @type proxy_serv_addr: C{tuple}

    @ivar out: File where to write reports. If it's not set, stdout will be
    used.
    @type out: C{str}

    @ivar save: File or directory name where the results will be written.
    @type save: C{str}

    @ivar keyfile: Key file for SSL connections.
    @type keyfile: C{str}

    @ivar certfile: Certificate to be used for SSL connections.
    @type certfile: C{str}

    @ivar clues: Sequence of clues obtained from the target.
    @type clues: C{list}

    @ivar analyzed: Sequence of clues after the analysis phase.
    @type analyzed: C{list}
    """
    def __init__(self):
        self.scantime = default_scantime
        self.parallelism = default_parallelism
        self.conf_file = default_conf_file
        self.verbose = False
        self.debug = False

        self.ratio_threshold = default_ratio_threshold

        self.urlfile = ''
        self.url = ''
        self.addr = ''

        self.proxy_serv_addr = ()

        self.save = ''

        self.out = default_out

        self.keyfile = None
        self.certfile = None

        self.clues = []
        self.analyzed = []


    def readConf(self):
        """Read configuration file.

        This method tries to read the specified configuration file. If we try
        to read it at the default path and it's not there we create a
        bare-bones file and use that one.

        @raise ConfError: If there's some problem creating or reading the
        configuration file.
        """
        # xxx - Move this into Halberd.conflib as a higher level function.

        reader = Halberd.conflib.ConfReader()

        try:
            reader.open(self.conf_file)
        except IOError:
            if self.conf_file == default_conf_file:
                try:
                    os.mkdir(default_conf_dir)
                    reader.writeDefault(default_conf_file)
                    reader.open(default_conf_file)
                except (OSError, IOError):
                    raise ConfError, 'unable to create a default conf. file'
            else:
                raise ConfError, 'unable to open configuration file %s\n'
        except conflib.InvalidConfFile:
            raise ConfError, 'invalid configuration file %s\n' % self.conf_file

        confvals = reader.parse()
        self.proxy_serv_addr = confvals[0]
        self.keyfile, self.certfile = confvals[1:]

        reader.close()


# vim: ts=4 sw=4 et
