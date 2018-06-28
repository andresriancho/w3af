"""
__init__.py

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
import os
import json
import time

from PyChromeDevTools import GenericElement, ChromeInterface

import w3af.core.controllers.output_manager as om


class DebugGenericElement(GenericElement):

    def __getattr__(self, attr):
        func_name = '{}.{}'.format(self.name, attr)

        def generic_function(**args):
            self.parent.pop_messages()
            self.parent.message_counter += 1

            message_id = self.parent.message_counter

            call_obj = {'id': message_id,
                        'method': func_name,
                        'params': args}
            call_str = json.dumps(call_obj, indent=4)

            self.parent.send(call_str)
            result, _ = self.parent.wait_result(message_id)

            return result

        return generic_function


class DebugChromeInterface(ChromeInterface):
    """
    The devtools protocol is documented at

        https://chromedevtools.github.io/devtools-protocol/

    Everything you can do with Chrome via this class is documented there,
    and since this class is very generic, it shouldn't require any changes
    to be able to consume all features.
    """
    message_counter = 0

    DEBUG = os.environ.get('DEBUG', '0') == '1'

    def send(self, data):
        self.debug('Sending message to Chrome: %s' % data)
        return self.ws.send(data)

    def recv(self):
        data = self.ws.recv()
        self.debug('Received message from Chrome: %s' % data)
        return data

    def wait_result(self, result_id, timeout=None):
        timeout = timeout if timeout is not None else self.timeout
        start_time = time.time()
        messages = []
        matching_result = None

        while True:
            now = time.time()
            if now-start_time > timeout:
                break

            try:
                message = self.recv()
            except Exception, e:
                msg = 'Unexpected error while reading from Chrome socket: "%s"'
                raise ChromeInterfaceException(msg % e)

            try:
                parsed_message = json.loads(message)
            except Exception, e:
                msg = 'Failed to parse JSON response from Chrome: "%s"'
                raise ChromeInterfaceException(msg % e)

            messages.append(parsed_message)

            if 'result' in parsed_message and parsed_message['id'] == result_id:
                matching_result = parsed_message
                break

            if 'error' in parsed_message:
                if 'message' in parsed_message['error']:
                    message = parsed_message['error']['message']
                    raise ChromeInterfaceException(message)
                else:
                    message = 'Unexpected error received from Chrome: "%s"'
                    raise ChromeInterfaceException(message % str(parsed_message))

        return matching_result, messages

    def debug(self, message):
        if not self.DEBUG:
            return

        print(message)

    def __getattr__(self, attr):
        generic_element = DebugGenericElement(attr, self)
        self.__setattr__(attr, generic_element)
        return generic_element


class ChromeInterfaceException(Exception):
    pass
