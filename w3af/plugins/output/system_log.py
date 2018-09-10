"""
system_log.py

Copyright 2018 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import syslog
import string

from w3af.core.controllers.plugins.output_plugin import OutputPlugin
from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.data.constants.severity import HIGH
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import BOOL, STRING
from w3af.core.data.options.option_list import OptionList
from w3af.plugins.output.console import catch_ioerror


class system_log(OutputPlugin):
    """
    Write log entries to Linux's syslog

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    # The message priority based on the python syslog module documentation [0] is:
    #
    #   LOG_EMERG, LOG_ALERT, LOG_CRIT, LOG_ERR,
    #   LOG_WARNING, LOG_NOTICE, LOG_INFO, LOG_DEBUG
    #
    # We'll match those to the levels we have in w3af.
    #
    # [0] https://docs.python.org/2/library/syslog.html

    def __init__(self):
        OutputPlugin.__init__(self)

        # User configured setting
        self.verbose = False
        self.scan_id = ''

    def _create_message(self, message):
        message = ''.join(ch for ch in message if ch in string.printable)
        return '[%s] %s' % (self.scan_id, message)

    @catch_ioerror
    def debug(self, message, new_line=True):
        """
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take
        an action for debug messages.
        """
        if self.verbose:
            message = self._create_message(message)
            syslog.syslog(syslog.LOG_DEBUG, message)

    @catch_ioerror
    def error(self, message, new_line=True, severity=None):
        message = self._create_message(message)
        syslog.syslog(syslog.LOG_ERR, message)

    def log_crash(self, message):
        message = self._create_message(message)
        syslog.syslog(syslog.LOG_CRIT, message)

    @catch_ioerror
    def console(self, message, new_line=True, severity=None):
        message = self._create_message(message)
        syslog.syslog(syslog.LOG_INFO, message)

    @catch_ioerror
    def vulnerability(self, message, new_line=True, severity=HIGH):
        message = self._create_message(message)
        syslog.syslog(syslog.LOG_WARNING, message)

    @catch_ioerror
    def information(self, message, new_line=True, severity=None):
        message = self._create_message(message)
        syslog.syslog(syslog.LOG_INFO, message)

    def set_options(self, option_list):
        """
        Sets the Options given on the OptionList to self. The options are the
        result of a user entering some data on a window that was constructed
        using the XML Options that was retrieved from the plugin using
        get_options()

        This method MUST be implemented on every plugin.

        :return: No value is returned.
        """
        self.verbose = option_list['verbose'].get_value()
        self.scan_id = option_list['scan_id'].get_value()

        if not self.scan_id:
            self.scan_id = rand_alnum(8)

        syslog.openlog('w3af', logoption=syslog.LOG_PID)

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Enable verbose output for syslog'
        o = opt_factory('verbose', self.verbose, d, BOOL)
        ol.add(o)

        d = 'String to be included in all syslog messages'
        h = 'Use this string to identify each individual scan in the log'
        o = opt_factory('scan_id', self.scan_id, d, STRING, help=h)
        ol.add(o)

        return ol

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin writes the framework messages to Linux's syslog.

        Two configurable parameters exist:
            - verbose
            - scan_id
            
        Use 'verbose' to indicate if debug messages should be sent to syslog,
        and 'scan_id' to configure a unique scan identifier that will be included
        in each message sent to syslog by this scan.
        
        Setting a 'scan_id' is useful to search through the logs and identify
        which message belongs to each scan. If this value is left empty a randomly
        generated ID will be used.
        
        Log lines generated by this plugin will have the following format:
        
            {date} {hostname} w3af[{PID}]: [{scan-id}] {message}
        
        Where the fields are defined as:
        
            - {date}: The log entry timestamp
            - {hostname}: The operating system host name
            - {PID}: The w3af process ID
            - {scan-id}: The configured scan identifier
            - {message}: Log message sent by w3af
        
        An example log line is:
        
            Sep  8 16:33:12 workstation w3af[2888]: [2k0jzvbwuk] Hello world!
        
        Different message priorities are used for debug, informational, error
        and vulnerability-related messages.
        """