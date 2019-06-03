"""
text_file.py

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
import time
import os

import w3af.core.data.kb.config as cf
import w3af.core.data.constants.severity as severity
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.output_plugin import OutputPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import OUTPUT_FILE
from w3af.core.data.options.output_file_option import DEV_NULL
from w3af.core.data.options.option_list import OptionList


REQUEST_HEADER_FMT = '=' * 40 + 'Request %s - %s ' + '=' * 40 + '\n'
RESPONSE_HEADER_FMT = '\n' + '=' * 40 + 'Response %s - %s ' + '=' * 39 + '\n'
LONG_LOG_FMT = '[%s - %s - %s] '
SHORT_LOG_FMT = '[%s - %s] '


class text_file(OutputPlugin):
    """
    Prints all messages to a text file.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        OutputPlugin.__init__(self)

        # User configured parameters
        self._output_file_name = '~/output.txt'
        self._http_file_name = '~/output-http.txt'
        self.verbose = True

        # Internal variables
        self._initialized = False

        # File handlers
        self._log = None
        self._http = None

        # XXX Only set '_show_caller' to True for debugging purposes. It
        # causes the execution of potentially slow code that handles
        # with introspection.
        self._show_caller = False

    def _init(self):
        
        self._initialized = True
        
        self._output_file_name = os.path.expanduser(self._output_file_name)
        self._http_file_name = os.path.expanduser(self._http_file_name)
        
        try:
            self._log = open(self._output_file_name,  'w')
        except IOError, io:
            msg = 'Can\'t open report file "%s" for writing, error: %s.'
            args = (os.path.abspath(self._output_file_name), io.strerror)
            raise BaseFrameworkException(msg % args)
        except Exception, e:
            msg = 'Can\'t open report file "%s" for writing, error: %s.'
            args = (os.path.abspath(self._output_file_name), e)
            raise BaseFrameworkException(msg % args)

        if self._http_file_name == DEV_NULL:
            # The user wants to ignore output to this file
            return

        try:
            # Images aren't ascii, so this file that logs every request/response,
            # will be binary.
            self._http = open(self._http_file_name, 'wb')
        except IOError, io:
            msg = 'Can\'t open HTTP report file "%s" for writing, error: %s.'
            args = (os.path.abspath(self._http_file_name), io.strerror)
            raise BaseFrameworkException(msg % args)
        except Exception, e:
            msg = 'Can\'t open HTTP report file "%s" for writing, error: %s.'
            args = (os.path.abspath(self._http_file_name), e)
            raise BaseFrameworkException(msg % args)

    def _write_to_file(self, msg, flush=False):
        """
        Write to the log file.

        :param msg: The text to write.
        """
        if self._log is None:
            return
        
        try:
            self._log.write(msg)
        except Exception, e:
            self._log = None
            msg = ('An exception was raised while trying to write to the output'
                   ' file "%s", error: "%s". Disabling output to this file.')
            om.out.error(msg % (self._output_file_name, e),
                         ignore_plugins={self.get_name()})

        if flush and self._log is not None:
            self._log.flush()

    def _write_to_http_log(self, msg):
        """
        Write to the HTTP log file.

        :param msg: The text to write (a string representation of the HTTP
                        request and response)
        """
        if self._http is None:
            return
        
        try:
            self._http.write(msg)
        except Exception, e:
            self._http = None
            msg = ('An exception was raised while trying to write to the output'
                   ' file "%s", error: "%s". Disabling output to this file.')
            om.out.error(msg % (self._http_file_name, e),
                         ignore_plugins={self.get_name()})

    def flush(self):
        """
        flush() the cache disk
        :return: None
        """
        if self._log is not None:
            self._log.flush()

        if self._http is not None:
            self._http.flush()

    def _clean_string_for_file(self, string_to_clean):
        """
        :param string_to_clean: A string that should be cleaned before using
                                it in a message object.
        """
        # https://github.com/andresriancho/w3af/issues/3586
        if string_to_clean is None:
            return ''

        # This will escape the string using \x00-style escapes, which is much
        # better than just printing null bytes (or any other non-printable char)
        # to the file
        return repr(string_to_clean)[1:-1]

    def write(self, message, log_type, new_line=True, flush=False):
        """
        Method that writes stuff to the text_file.

        :param message: The message to write to the file
        :param log_type: Type of message are we writing to the file
        :param new_line: Add a new line after the message
        """
        if not self._initialized:
            self._init()

        to_print = str(message)
        to_print = self._clean_string_for_file(to_print)

        if new_line:
            to_print += '\n'

        now = time.localtime(time.time())
        the_time = time.strftime("%c", now)

        if self._show_caller:
            timestamp = LONG_LOG_FMT % (the_time, log_type, self.get_caller())
        else:
            timestamp = SHORT_LOG_FMT % (the_time, log_type)

        self._write_to_file(timestamp + to_print, flush=flush)

    def debug(self, message, new_line=True):
        """
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action for debug messages.
        """
        if self.verbose:
            self.write(message, 'debug', new_line)

    def information(self, message, new_line=True):
        """
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action for informational messages.
        """
        self.write(message, 'information', new_line)

    def error(self, message, new_line=True):
        """
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action for error messages.
        """
        self.write(message, 'error', new_line, flush=True)

    def vulnerability(self, message, new_line=True, severity=severity.MEDIUM):
        """
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action when a vulnerability is found.
        """
        self.write(message, 'vulnerability', new_line)

    def console(self, message, new_line=True):
        """
        This method is used by the w3af console to print messages to the outside
        """
        self.write(message, 'console', new_line)

    def log_enabled_plugins(self, plugins_dict, options_dict):
        """
        This method is called from the output manager object. This method should
        take an action for the enabled plugins and their configuration. Usually,
        write the info to a file or print it somewhere.

        :param plugins_dict: A dict with all the plugin types and the enabled
                                plugins for that type of plugin.
        :param options_dict: A dict with the options for every plugin.
        """
        now = time.localtime(time.time())
        the_time = time.strftime("%c", now)
        timestamp = '[ %s - Enabled plugins ] ' % the_time

        to_print = ''

        for plugin_type in plugins_dict:
            to_print += self._create_plugin_info(plugin_type,
                                                 plugins_dict[plugin_type],
                                                 options_dict[plugin_type])

        # And now the target information
        str_targets = ', '.join([u.url_string for u in cf.cf.get('targets')])
        to_print += 'target\n'
        to_print += '    set target ' + str_targets + '\n'
        to_print += '    back'

        to_print = to_print.replace('\n', '\n' + timestamp) + '\n'

        self._write_to_file(timestamp + to_print)

    def end(self):
        if self._http is not None:
            self._http.close()

        if self._log is not None:
            self._log.close()

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
        self._output_file_name = option_list['output_file'].get_value()
        self._http_file_name = option_list['http_output_file'].get_value()

        self._init()

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Enable if verbose output is needed'
        o = opt_factory('verbose', self.verbose, d, 'boolean')
        ol.add(o)

        d = 'File name where this plugin will write to'
        o = opt_factory('output_file', self._output_file_name, d, OUTPUT_FILE)
        ol.add(o)

        d = 'File name where this plugin will write HTTP requests and responses'
        o = opt_factory('http_output_file', self._http_file_name, d, OUTPUT_FILE)
        ol.add(o)

        return ol

    def log_http(self, request, response):
        """
        log the http req / res to file.
        :param request: A fuzzable request object
        :param response: A HTTPResponse object
        """
        if self._http_file_name == DEV_NULL:
            # We could open() /dev/null, write to that file, and leave the code
            # as-is (without this if statement).
            #
            # But that would require w3af to dump() request and response,
            # serialize all that into strings, and write them to /dev/null
            #
            # After all the CPU effort, that data will be discarded... a complete
            # waste of time!
            #
            # So we just check if the output is /dev/null and return
            return

        now = time.localtime(time.time())
        the_time = time.strftime("%c", now)

        request_hdr = REQUEST_HEADER_FMT % (response.id, the_time)
        self._write_to_http_log(request_hdr)
        self._write_to_http_log(request.dump())
        
        response_hdr = RESPONSE_HEADER_FMT % (response.id, the_time)
        self._write_to_http_log(response_hdr)
        self._write_to_http_log(response.dump())

        self._write_to_http_log('\n' + '=' * (len(request_hdr) - 1) + '\n')

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin writes the framework messages to a text file.

        Three configurable parameters exist:
            - output_file
            - http_output_file
            - verbose
        
        Use `dev/null` as the value for any of the output file options to
        disable writing to that log.
        """
