"""
helpers.py

Copyright 2013 Andres Riancho

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
import cgi
import ssl
import socket
import urllib
import urllib2
import httplib

from errno import (ECONNREFUSED, EHOSTUNREACH, ECONNRESET, ENETDOWN,
                   ENETUNREACH, ETIMEDOUT, ENOSPC)

from w3af.core.controllers.exceptions import HTTPRequestException
from w3af.core.data.url.handlers.keepalive import URLTimeoutError
from w3af.core.data.constants.response_codes import NO_CONTENT
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers

from w3af.core.controllers.misc.number_generator import consecutive_number_generator


def new_no_content_resp(uri, add_id=False):
    """
    Return a new NO_CONTENT HTTPResponse object.
    
    :param uri: URI string or request object
    """
    no_content_response = HTTPResponse(NO_CONTENT, '', Headers(), uri,
                                       uri, msg='No Content')

    if add_id:
        no_content_response.id = consecutive_number_generator.inc()

    return no_content_response


def get_clean_body(mutant, response):
    """
    @see: Very similar to fingerprint_404.py get_clean_body() bug not quite
          the same maybe in the future I can merge both?

    Definition of clean in this method:
        - input:
            - response.get_url() == http://host.tld/aaaaaaa/?id=1 OR 23=23
            - response.get_body() == '...<x>1 OR 23=23</x>...'

        - output:
            - self._clean_body( response ) == '...<x></x>...'

    All injected values are removed encoded and "as is".

    :param mutant: The mutant where I can get the value from.
    :param response: The HTTPResponse object to clean
    :return: A string that represents the "cleaned" response body.
    """

    body = response.body

    if response.is_text_or_html():
        mod_value = mutant.get_token_value()

        body = body.replace(mod_value, '')
        body = body.replace(urllib.unquote_plus(mod_value), '')
        body = body.replace(cgi.escape(mod_value), '')
        body = body.replace(cgi.escape(urllib.unquote_plus(mod_value)), '')

    return body


def get_socket_exception_reason(error):
    """
    :param error: The socket.error exception instance
    :return: The reason/message associated with that exception
    """
    if not isinstance(error, socket.error):
        return

    # Known reason errors. See errno module for more info on these errors
    EUNKNSERV = -2      # Name or service not known error
    EINVHOSTNAME = -5   # No address associated with hostname
    known_errors = (EUNKNSERV, ECONNREFUSED, EHOSTUNREACH, ECONNRESET,
                    ENETDOWN, ENETUNREACH, EINVHOSTNAME, ETIMEDOUT, ENOSPC)

    if error[0] in known_errors:
        return str(error)

    return


def get_exception_reason(error):
    """
    :param error: The exception instance
    :return: The reason/message associated with that exception (if known)
             else we return None.
    """
    reason_msg = None

    if isinstance(error, URLTimeoutError):
        # New exception type raised by keepalive handler
        reason_msg = error.message

    # Exceptions may be of type httplib.HTTPException or socket.error
    # We're interested on handling them in different ways
    elif isinstance(error, urllib2.URLError):
        reason_err = error.reason

        if isinstance(reason_err, socket.error):
            reason_msg = get_socket_exception_reason(error)

    elif isinstance(error, (ssl.SSLError, socket.sslerror)):
        socket_reason = get_socket_exception_reason(error)
        if socket_reason:
            reason_msg = 'SSL Error: %s' % socket_reason

    elif isinstance(error, socket.error):
        reason_msg = get_socket_exception_reason(error)

    elif isinstance(error, HTTPRequestException):
        reason_msg = error.value

    elif isinstance(error, httplib.BadStatusLine):
        reason_msg = 'Bad HTTP response status line: %s' % error.line

    elif isinstance(error, httplib.HTTPException):
        #
        # Here we catch:
        #
        #    ResponseNotReady, CannotSendHeader, CannotSendRequest,
        #    ImproperConnectionState,
        #    IncompleteRead, UnimplementedFileMode, UnknownTransferEncoding,
        #    UnknownProtocol, InvalidURL, NotConnected.
        #
        #    TODO: Maybe we're being TOO generic in this isinstance?
        #
        reason_msg = '%s: %s' % (error.__class__.__name__,
                                 error.args)

    return reason_msg