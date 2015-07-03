"""
log_handler.py

Copyright 2015 Andres Riancho

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

from w3af.core.data.db.disk_list import DiskList
from w3af.core.data.db.disk_item import DiskItem
from w3af.core.data.constants.severity import MEDIUM
from w3af.core.controllers.plugins.output_plugin import OutputPlugin

DEBUG = 'debug'
INFORMATION = 'information'
ERROR = 'error'
VULNERABILITY = 'vulnerability'
CONSOLE = 'console'
LOG_HTTP = 'log_http'


class RESTAPIOutput(OutputPlugin):
    """
    Store all log messages on a DiskList

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        super(RESTAPIOutput, self).__init__()
        self.log = DiskList(table_prefix='RestApiScanLog')
        self.log_id = -1

    def get_log_id(self):
        self.log_id += 1
        return self.log_id

    def debug(self, msg_string, new_line=True):
        """
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action for debug messages.
        """
        m = Message(DEBUG, self._clean_string(msg_string), self.get_log_id())
        self.log.append(m)

    def information(self, msg_string, new_line=True):
        """
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action for informational messages.
        """
        m = Message(INFORMATION, self._clean_string(msg_string),
                    self.get_log_id())
        self.log.append(m)

    def error(self, msg_string, new_line=True):
        """
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action for error messages.
        """
        m = Message(ERROR, self._clean_string(msg_string), self.get_log_id())
        self.log.append(m)

    def vulnerability(self, msg_string, new_line=True, severity=MEDIUM):
        """
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action when a vulnerability is found.
        """
        m = Message(VULNERABILITY, self._clean_string(msg_string),
                    self.get_log_id())
        m.set_severity(severity)
        self.log.append(m)

    def console(self, msg_string, new_line=True):
        """
        This method is used by the w3af console to print messages to the outside
        """
        m = Message(CONSOLE, self._clean_string(msg_string), self.get_log_id())
        self.log.append(m)


class Message(DiskItem):
    def __init__(self, msg_type, msg, _id):
        """
        :param msg_type: console, information, vulnerability, etc
        :param msg: The message itself
        """
        self._type = msg_type
        self._msg = msg
        self._time = time.time()
        self._severity = None
        self._id = _id

    def get_id(self):
        return self._id

    def get_severity(self):
        return self._severity

    def set_severity(self, the_severity):
        self._severity = the_severity

    def get_msg(self):
        return self._msg

    def get_type(self):
        return self._type

    def get_real_time(self):
        return self._time

    def get_time(self):
        return time.strftime('%c', time.localtime(self._time))

    def to_json(self):
        return {'type': self._type,
                'message': self._msg,
                'time': self.get_time(),
                'severity': self.get_severity(),
                'id': self.get_id()}

    def get_eq_attrs(self):
        return ('_type', '_msg', '_time', '_severity', '_id')