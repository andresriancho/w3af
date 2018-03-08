"""
console.py

Copyright 2006 Andres Riancho

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
import sys
import string

from errno import ENOSPC
from functools import wraps
from termcolor import colored

from w3af.core.data.constants.severity import HIGH, MEDIUM, LOW, INFORMATION
from w3af.core.controllers.plugins.output_plugin import OutputPlugin
from w3af.core.controllers.exceptions import ScanMustStopByKnownReasonExc
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import BOOL
from w3af.core.data.options.option_list import OptionList


ERROR = 'Error'


def catch_ioerror(meth):
    """
    Function to decorate methods in order to catch IOError exceptions.
    """
    @wraps(meth)
    def wrapper(self, *args, **kwargs):
        try:
            return meth(self, *args, **kwargs)
        except IOError as (errno, strerror):
            if errno == ENOSPC:
                msg = 'No space left on device'
                raise ScanMustStopByKnownReasonExc(msg)

    return wrapper


class console(OutputPlugin):
    """
    Print messages to the console.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    SEVERITY_COLOR = {HIGH: 'red',
                      MEDIUM: 'yellow',
                      LOW: 'blue',
                      INFORMATION: 'cyan',
                      ERROR: 'white'}

    def __init__(self):
        OutputPlugin.__init__(self)

        # User configured setting
        self.verbose = False
        self.use_colors = True

    def _make_printable(self, a_string):
        a_string = str(a_string)
        a_string = a_string.replace('\n', '\n\r')
        return ''.join(ch for ch in a_string if ch in string.printable)

    def _print_to_stdout(self, message, newline, severity=None):
        message = self._make_printable(message)
        if newline:
            message += '\r\n'

        if self.use_colors:
            color = self.SEVERITY_COLOR.get(severity, None)
            if color is not None:
                message = colored(message, color)

        sys.stdout.write(message)
        sys.stdout.flush()

    @catch_ioerror
    def debug(self, message, new_line=True):
        """
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take
        an action for debug messages.
        """
        if self.verbose:
            self._print_to_stdout(message, new_line)

    @catch_ioerror
    def error(self, message, new_line=True, severity=None):
        self._print_to_stdout(message, new_line, severity=ERROR)

    @catch_ioerror
    def console(self, message, new_line=True, severity=None):
        self._print_to_stdout(message, new_line)

    @catch_ioerror
    def vulnerability(self, message, new_line=True, severity=HIGH):
        self._print_to_stdout(message, new_line, severity=severity)

    @catch_ioerror
    def information(self, message, new_line=True, severity=None):
        self._print_to_stdout(message, new_line)

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
        self.use_colors = option_list['use_colors'].get_value()

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Enables verbose output for the console'
        o = opt_factory('verbose', self.verbose, d, BOOL)
        ol.add(o)

        d = 'Enable output coloring'
        o = opt_factory('use_colors', self.use_colors, d, BOOL)
        ol.add(o)

        return ol

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin writes the framework messages to the console.

        Two configurable parameters exist:
            - verbose
            - use_colors
        """