"""
devtools.py

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
import logging

from PyChromeDevTools import GenericElement, ChromeInterface, TIMEOUT
from websocket import WebSocketTimeoutException

import w3af.core.controllers.output_manager as om
from w3af.core.controllers.tests.running_tests import is_running_tests

#
# Disable all the annoying logging from the urlli3 and requests libraries
#
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class DebugGenericElement(GenericElement):

    def __getattr__(self, attr):
        func_name = '{}.{}'.format(self.name, attr)

        def generic_function(**kwargs):
            self.parent.pop_messages()
            self.parent.message_counter += 1

            timeout = kwargs.pop('timeout', 20)

            message_id = self.parent.message_counter

            call_obj = {'id': message_id,
                        'method': func_name,
                        'params': kwargs}
            call_str = json.dumps(call_obj, indent=4)

            self.parent.send(call_str)
            result, _ = self.parent.wait_result(message_id, timeout=timeout)

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

    def __init__(self, host='localhost', port=9222, tab=0, timeout=TIMEOUT, auto_connect=True, debugging_id=None):
        super(DebugChromeInterface, self).__init__(host=host, port=port, tab=tab, timeout=timeout, auto_connect=auto_connect)
        self.debugging_id = debugging_id

    def set_debugging_id(self, debugging_id):
        self.debugging_id = debugging_id

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
                data = self.recv()
            except WebSocketTimeoutException:
                continue
            except Exception, e:
                msg = 'Unexpected error while reading from Chrome socket: "%s"'
                raise ChromeInterfaceException(msg % e)

            try:
                message = json.loads(data)
            except Exception, e:
                msg = 'Failed to parse JSON response from Chrome: "%s"'
                raise ChromeInterfaceException(msg % e)

            messages.append(message)

            #
            # Now we handle the message
            #
            error_code = message.get('result', {}).get('errorText', '')

            if error_code == 'net::ERR_PROXY_CONNECTION_FAILED':
                raise ChromeInterfaceException('Chrome failed to connect to proxy server')

            if 'result' in message and message['id'] == result_id:
                matching_result = message
                break

            if 'error' in message:
                if 'message' in message['error']:
                    message = message['error']['message']
                    raise ChromeInterfaceException(message)
                else:
                    message = 'Unexpected error received from Chrome: "%s"'
                    raise ChromeInterfaceException(message % str(message))

        return matching_result, messages

    def wait_event(self, event, timeout=None):
        timeout = timeout if timeout is not None else self.timeout
        start_time = time.time()
        messages = []
        matching_message = None

        while True:

            # break on timeout
            now = time.time()
            if now-start_time > timeout:
                break

            try:
                message = self.recv()
            except Exception:
                # Continue on websocket timeout, by default this is triggered
                # every 1 second
                continue
            
            try:
                parsed_message = json.loads(message)
            except ValueError:
                # If we received an invalid JSON from Chrome, we ignore it and
                # continue to receive the next one
                continue

            messages.append(parsed_message)

            if 'method' in parsed_message and parsed_message['method'] == event:
                matching_message = parsed_message
                break

        return matching_message, messages

    def debug(self, message):
        if not self.DEBUG:
            return

        message = '(did: %s) %s' % (self.debugging_id, message)

        if is_running_tests():
            print(message)
        else:
            om.out.debug(message)

    def __getattr__(self, attr):
        generic_element = DebugGenericElement(attr, self)
        self.__setattr__(attr, generic_element)
        return generic_element


class ChromeInterfaceException(Exception):
    pass
