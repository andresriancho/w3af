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
import pprint
import logging

from collections import deque
from PyChromeDevTools import GenericElement, ChromeInterface, TIMEOUT
from websocket import WebSocketTimeoutException

import w3af.core.controllers.output_manager as om
from w3af.core.controllers.tests.running_tests import is_running_tests

#
# Disable all the annoying logging from the urlli3 and requests libraries
#
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


# This is the default dialog handler, it is used to dismiss alert, prompt, etc.
# which might appear during crawling.
def dialog_handler(_type, message):
    """
    Handles Page.javascriptDialogOpening event [0] which freezes the browser
    until it is dismissed.

    [0] https://chromedevtools.github.io/devtools-protocol/tot/Page#event-javascriptDialogOpening

    :param _type: One of alert, prompt, etc.
    :param message: The message shown in the aler / prompt
    :return: A tuple containing:
                * True if we want to dismiss the alert / prompt or False if we
                  want to cancel it.

                * The message to enter in the prompt (if this is a prompt).
    """
    return True, 'Bye!'


DEFAULT_DIALOG_HANDLER = dialog_handler


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
            call_str = json.dumps(call_obj)

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

    def __init__(self,
                 host='localhost',
                 port=9222,
                 tab=0,
                 timeout=TIMEOUT,
                 auto_connect=True,
                 debugging_id=None,
                 dialog_handler=DEFAULT_DIALOG_HANDLER):
        super(DebugChromeInterface, self).__init__(host=host,
                                                   port=port,
                                                   tab=tab,
                                                   timeout=timeout,
                                                   auto_connect=auto_connect)
        self.debugging_id = debugging_id
        self.dialog_handler = dialog_handler
        self.console = deque(maxlen=500)

    def set_debugging_id(self, debugging_id):
        self.debugging_id = debugging_id

    def set_dialog_handler(self, dialog_handler):
        self.dialog_handler = dialog_handler

    def send(self, data):
        self.debug('Sending message to Chrome: %s' % data)
        return self.ws.send(data)

    def recv(self):
        data = self.ws.recv()
        self.debug('Received message from Chrome: %s' % data)
        return data

    def close(self):
        super(DebugChromeInterface, self).close()
        self.ws = None

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

            self._handle_received_message(message)

            if 'result' in message and message['id'] == result_id:
                matching_result = message
                break

        return matching_result, messages

    def wait_event(self, event, name=None, timeout=None):
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

            self._handle_received_message(parsed_message)

            method = parsed_message.get('method', None)
            if method is None:
                continue

            if method != event:
                continue

            if name is None:
                matching_message = parsed_message
                break

            received_name = parsed_message.get('params', {}).get('name', None)
            if received_name is None:
                continue

            if received_name == name:
                matching_message = parsed_message
                break

        return matching_message, messages

    def _handle_received_message(self, message):
        """
        This method handles the messages we receive from Chrome in both:
            - wait_event
            - wait_result

        The main goal of the method is to capture any errors Chrome might
        have returned and handle them by raising exceptions, increasing
        timeouts, etc.

        :param message: A dict containing the message received from Chrome
        :return: None
        """
        error_code = message.get('result', {}).get('errorText', '')

        if error_code == 'net::ERR_PROXY_CONNECTION_FAILED':
            raise ChromeInterfaceException('Chrome failed to connect to proxy server')

        if 'method' in message:
            # Handle alert, prompt, etc.
            if message['method'] == 'Page.javascriptDialogOpening':
                params = message['params']

                message = params['message']
                _type = params['type']

                # Get the action to take (accept or cancel) and the message to
                # type in the prompt() - if any - from the dialog handler and
                # send it to Chrome
                dismiss, response_message = self.dialog_handler(_type, message)
                self.Page.handleJavaScriptDialog(accept=dismiss,
                                                 promptText=response_message)

            elif message['method'] == 'Runtime.consoleAPICalled':
                params = message['params']
                _type = params['type']
                args = params['args']
                self.console.append(ConsoleMessage(_type, args))

        if 'error' in message:
            if 'message' in message['error']:
                message = message['error']['message']
                raise ChromeInterfaceException(message)
            else:
                message = 'Unexpected error received from Chrome: "%s"'
                raise ChromeInterfaceException(message % str(message))

    def debug(self, message):
        if not self.DEBUG:
            return

        message = '(did: %s) %s' % (self.debugging_id, message)

        if is_running_tests():
            print(message)
        else:
            om.out.debug(message)

    def read_console_message(self):
        """
        Reads one console log message from the deque and returns it.

        Note that by reading the message you are removing it from the
        dequeue and won't be able to read the same message again.

        :return: A ConsoleMessage instance, or None if the deque is empty
        """
        try:
            return self.console.popleft()
        except IndexError:
            return None

    def __getattr__(self, attr):
        generic_element = DebugGenericElement(attr, self)
        self.__setattr__(attr, generic_element)
        return generic_element


class ChromeInterfaceException(Exception):
    pass


class ConsoleMessage(object):
    __slots__ = ('type', 'message', 'args')

    def __init__(self, _type, args):
        self.type = _type
        self.args = args
        self.message = self.get_message(args)

    def get_message(self, args):
        """
        When console.log('hello world') is called, the event args looks like:

            [{"type":"string","value":"hello world"}]

        This method extracts the value only if the args list has one item
        and the type is a string.

        :param args: The arguments passed to console.log
        :return: The message (if any) as a string
        """
        if not len(args) == 1:
            return None

        arg = args[0]

        _type = arg.get('type', None)
        if _type != 'string':
            return None

        value = arg.get('value', None)
        if value is None:
            return None

        return value

    def __str__(self):
        data = self.message if self.message is not None else '\n%s' % pprint.pformat(self.args, indent=4)
        return '<ConsoleMessage(%s): "%s">' % (self.type, data)

    __repr__ = __str__
