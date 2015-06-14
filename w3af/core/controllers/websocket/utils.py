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

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.exceptions import (BaseFrameworkException,
                                              HTTPRequestException)
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
    """
    Create a GET request with the required HTTP headers to upgrade to web
    sockets

    :param web_socket_url: The URL instance where to upgrade
    :param extra_headers: Any extra headers that will override the defaults
    :param web_socket_version: The websocket version to use
    :param origin: Origin header value
    :return: An HTTP request
    """
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
    else:
        # If no origin is specified, guess:
        scheme = 'https://' if 'wss://' in web_socket_url else 'http://'
        args = (scheme, web_socket_url.get_domain())
        request_headers['Origin'] = '%s%s' % args

    # Replace the protocol so we can easily send a request
    forged_url = web_socket_url.url_string.replace('wss://', 'https://', 1)
    forged_url = forged_url.replace('ws://', 'http://', 1)
    forged_url = URL(forged_url)

    upgrade_request = FuzzableRequest(forged_url, 'GET',
                                      headers=request_headers)
    return upgrade_request


def negotiate_websocket_version(uri_opener, websocket_url):
    """
    Try to find the websocket version used to talk to the server

    :param uri_opener: A URL opener
    :param websocket_url: The web socket URL instance
    :return: The websocket version to use
    """
    for version in {13, 12, 14}:
        upgrade_request = build_ws_upgrade_request(websocket_url,
                                                   web_socket_version=version)

        try:
            upgrade_response = uri_opener.send_mutant(upgrade_request)
        except HTTPRequestException:
            # Some rather unfriendly web socket servers simply close the
            # connection when there is a protocol mismatch
            continue

        upgrade_code = upgrade_response.get_code()

        if upgrade_code in {101}:
            return version

        elif upgrade_code in {400}:
            # Might be because of an incorrect protocol version, some web
            # servers are really nice and tell us which version they want to
            # use, others simply say: "400" and nothing else
            headers = upgrade_response.get_headers()
            version, _ = headers.iget('Sec-WebSocket-Version', None)

            if version is None:
                # Test the next version
                continue

            return version

        else:
            # The other response codes can be anything from "I don't speak that
            # websocket protocol" to "here is my 404 page"
            #
            # Another option is that we're connecting to the web socket using
            # an origin that's not allowed, in some cases that's a 403 forbidden
            continue

    # I want to be very friendly and when I'm not aware of the real version just
    # return the default one
    return DEFAULT_PROTOCOL_VERSION


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

    # Relaxed check
    if upgrade_value and connection_value and sec_websocket_accept_value:
        return True

    return False


class WebSocketProtocolException(BaseFrameworkException):
    pass