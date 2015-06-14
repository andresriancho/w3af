"""
utils.py

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
import base64
import string
import random

from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.constants.websockets import (WEBSOCKET_UPGRADE_HEADERS,
                                                 DEFAULT_PROTOCOL_VERSION)


def gen_ws_sec_key():
    _set = string.ascii_uppercase + string.digits
    key = ''.join(random.choice(_set) for _ in range(16))
    return base64.b64encode(key)


def build_ws_upgrade_request(web_socket_url, extra_headers=None,
                             web_socket_version=DEFAULT_PROTOCOL_VERSION,
                             origin=None):
    # Replace the protocol so we can easily send a request
    web_socket_url = web_socket_url.replace('wss://', 'https://', 1)
    web_socket_url = web_socket_url.replace('ws://', 'http://', 1)

    request_headers = Headers()
    request_headers['Sec-WebSocket-Key'] = gen_ws_sec_key()

    for key, value in WEBSOCKET_UPGRADE_HEADERS.items():
        request_headers[key] = value

    if extra_headers is not None:
        for key, value in extra_headers:
            request_headers[key] = value

    # Allows me to connect to web socket endpoints with different versions
    request_headers['Sec-WebSocket-Version'] = str(web_socket_version)

    if origin is not None:
        request_headers['Origin'] = origin

    upgrade_request = FuzzableRequest(web_socket_url, 'GET',
                                      headers=request_headers)
    return upgrade_request


def negotiate_websocket_version(uri_opener, websocket_url):
    upgrade_request = build_ws_upgrade_request(websocket_url)

    upgrade_response = uri_opener.send_mutant(upgrade_request)
    upgrade_code = upgrade_response.get_code()

    if upgrade_code in {200, 301, 302, 303, 404, 403, 500}:
        msg = 'Unexpected WebSockets response code: %s' % upgrade_code
        raise WebSocketProtocolException(msg)

    if upgrade_code in {400}:
        # Might be because of an incorrect protocol version
        headers = upgrade_response.get_headers()
        version, _ = headers.iget('Sec-WebSocket-Version', None)

        if version is None:
            msg = 'Missing Sec-WebSocket-Version header in protocol upgrade'
            raise WebSocketProtocolException(msg)

        return version

    if upgrade_code in {101}:
        return DEFAULT_PROTOCOL_VERSION

    # TODO: I'm not sure what happens here. What if I'm in a case where the
    #       WebSocket is not answering with the expected 101 because the
    #       origin is incorrect, or cookies are missing? What's the expected
    #       answer for a websocket server in that case?
    raise NotImplementedError


def is_successful_upgrade(upgrade_response):
    """
    Match against:

        HTTP/1.1 101 Switching Protocols
        Upgrade: websocket
        Connection: Upgrade
        Sec-WebSocket-Accept: HSmrc0sMlYUkAGmm5OPpG2HaGWk=
        Sec-WebSocket-Protocol: chat

    :see: https://en.wikipedia.org/wiki/WebSocket

    :param upgrade_response: The HTTP response
    :return: True if the response is a successful upgrade
    """
    if upgrade_response.get_code() != 101:
        return False

    headers = upgrade_response.get_headers()

    upgrade_value, _ = headers.iget('Upgrade', None)
    connection_value, _ = headers.iget('Connection', None)
    sec_websocket_accept_value, _ = headers.iget('Sec-WebSocket-Accept', None)

    if upgrade_value and connection_value and sec_websocket_accept_value:
        return True

    return False


class WebSocketProtocolException(BaseFrameworkException):
    pass