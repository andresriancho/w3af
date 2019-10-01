"""
event_handlers.py

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

from w3af.core.controllers.chrome.devtools.exceptions import ChromeInterfaceException


NET_ERRORS = {'net::ERR_EMPTY_RESPONSE',
              'net::ERR_ABORTED',
              'net::ERR_CONNECTION_RESET',
              'net::ERR_NETWORK_CHANGED',
              'net::ERR_INTERNET_DISCONNECTED',
              'net::ERR_CONNECTION_TIMED_OUT',
              'net::ERR_SSL_PROTOCOL_ERROR'}


def proxy_connection_failed_handler(message):
    error_code = message.get('result', {}).get('errorText', '')

    if error_code == 'net::ERR_PROXY_CONNECTION_FAILED':
        raise ChromeInterfaceException('Chrome failed to connect to proxy server')


def net_errors_handler(message):
    error_code = message.get('result', {}).get('errorText', '')

    if error_code in NET_ERRORS:
        msg = 'Chrome failed to connect to target host: "%s"'
        raise ChromeInterfaceException(msg % error_code)


def generic_error_handler(message):
    if 'error' not in message:
        return

    if 'message' in message['error']:
        message = message['error']['message']
        raise ChromeInterfaceException(message)
    else:
        message = 'Unexpected error received from Chrome: "%s"'
        raise ChromeInterfaceException(message % str(message))


def inspector_crash_handler(message):
    if 'method' not in message:
        return

    if 'Inspector.targetCrashed' == message['method']:
        raise ChromeInterfaceException('The remote inspector crashed!')
