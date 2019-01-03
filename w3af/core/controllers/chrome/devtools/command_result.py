"""
command_result.py

Copyright 2019 Andres Riancho

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
import threading

from w3af.core.controllers.chrome.devtools.exceptions import ChromeInterfaceTimeout


class CommandResult(object):
    def __init__(self, message_id):
        self.message_id = message_id
        self.message = None
        self.id_handler = None
        self.event = threading.Event()
        self.exc_type = None
        self.exc_value = None
        self.exc_traceback = None

    def get(self, timeout):
        # Raise any exceptions right away
        self._raise_exception_if_exists()

        was_set = self.event.wait(timeout=timeout)

        # Or after the timeout, exceptions might have appeared while the
        # timeout was running
        self._raise_exception_if_exists()

        if not was_set:
            raise ChromeInterfaceTimeout('Timeout')

        return self.message

    def set(self, message):
        self.message = message
        self.event.set()

    def set_exception(self, exc_type, exc_value, exc_traceback):
        self.exc_type = exc_type
        self.exc_value = exc_value
        self.exc_traceback = exc_traceback
        self.event.set()

    def set_id_handler(self, id_handler):
        self.id_handler = id_handler

    def get_id_handler(self):
        return self.id_handler

    def _raise_exception_if_exists(self):
        if self.exc_type is None:
            return

        raise self.exc_type, self.exc_value, self.exc_traceback
