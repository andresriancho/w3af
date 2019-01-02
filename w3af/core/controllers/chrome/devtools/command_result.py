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

    def get(self, timeout):
        was_set = self.event.wait(timeout=timeout)

        if not was_set:
            raise ChromeInterfaceTimeout('Timeout')

        return self.message

    def set(self, message):
        self.message = message
        self.event.set()

    def set_id_handler(self, id_handler):
        self.id_handler = id_handler

    def get_id_handler(self):
        return self.id_handler
