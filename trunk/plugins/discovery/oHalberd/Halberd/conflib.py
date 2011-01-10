# -*- coding: iso-8859-1 -*-

"""Configuration file management module.

Halberd uses configuration files to store relevant information needed for
certain protocols (SSL) or modes of operation (proxy, distributed
client/server, etc.).

This module takes care of reading and writing configuration files.

@var default_proxy_port: Default TCP port to listen when acting as a proxy.
@type default_proxy_port: C{int}
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
import ConfigParser


default_proxy_port = 8080

default_conf = r"""
# ============================================================================
# halberd configuration file.
# ============================================================================

[proxy]

address:
port: 8080

[ssl]

keyfile:
certfile:
"""


class InvalidConfFile(Exception):
    """Invalid configuration file.
    """


class ConfReader:
    """Takes care of turning configuration files into meaningful information.
    """

    def __init__(self):
        self.__dict = {}
        self.__conf = None

        self.confparser = ConfigParser.SafeConfigParser()

    def open(self, fname):
        """Opens the configuration file.

        @param fname: Pathname to the configuration file.
        @type fname: C{str}

        @raise InvalidConfFile: In case the passed file is not a valid one.
        """
        self.__conf = open(os.path.expanduser(fname), 'r')
        try:
            self.confparser.readfp(self.__conf, fname)
        except ConfigParser.MissingSectionHeaderError, msg:
            raise InvalidConfFile, msg

    def close(self):
        """Release the configuration file's descriptor.
        """
        if self.__conf:
            self.__conf.close()


    def _getAddr(self, sectname, default_port):
        """Read a network address from the given section.
        """
        section = self.__dict[sectname]
        addr = section.get('address', '')
        try:
            port = int(section.get('port', default_port))
        except ValueError:
            port = default_port

        return (addr, port)

    def parse(self):
        """Parses the configuration file.
        """
        assert self.__conf, 'The configuration file is not open'

        proxy_serv_addr = ()

        # The orthodox way of doing this is via ConfigParser.get*() but those
        # methods lack the convenience of dict.get. While another approach
        # could be to subclass ConfigParser I think it's overkill for the
        # current situation.
        for section in self.confparser.sections():
            sec = self.__dict.setdefault(section, {})
            for name, value in self.confparser.items(section):
                sec.setdefault(name, value)

        if self.__dict.has_key('proxy'):
            proxy_serv_addr = self._getAddr('proxy', default_proxy_port)

        keyfile = self.__dict['ssl'].get('keyfile', None)
        certfile = self.__dict['ssl'].get('certfile', None)

        if keyfile == '':
            keyfile = None
        if certfile == '':
            certfile = None

        return proxy_serv_addr, keyfile, certfile

    def writeDefault(self, conf_file):
        """Write a bare-bones configuration file

        @param conf_file: Target file where the default conf. will be written.
        @type conf_file: C{str}
        """
        assert conf_file and isinstance(conf_file, basestring)

        conf_fp = open(conf_file, 'w')
        conf_fp.write(default_conf)
        conf_fp.close()


    def __del__(self):
        self.close()


# vim: ts=4 sw=4 et
