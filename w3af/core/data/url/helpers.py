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
import OpenSSL

from errno import (ECONNREFUSED, EHOSTUNREACH, ECONNRESET, ENETDOWN,
                   ENETUNREACH, ETIMEDOUT, ENOSPC)

from w3af.core.data.misc.encoding import smart_unicode, PERCENT_ENCODE
from w3af.core.controllers.exceptions import HTTPRequestException
from w3af.core.data.url.handlers.keepalive import URLTimeoutError
from w3af.core.data.constants.response_codes import NO_CONTENT
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers

from w3af.core.controllers.misc.number_generator import consecutive_number_generator

# Known reason errors. See errno module for more info on these errors
EUNKNSERV = -2        # Name or service not known error
EINVHOSTNAME = -5     # No address associated with hostname
EUNEXPECTEDEOF = -1   # https://github.com/andresriancho/w3af/issues/10290

KNOWN_SOCKET_ERRORS = (EUNKNSERV, ECONNREFUSED, EHOSTUNREACH, ECONNRESET,
                       ENETDOWN, ENETUNREACH, EINVHOSTNAME, ETIMEDOUT,
                       ENOSPC, EUNEXPECTEDEOF)


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

        # Since the body is already in unicode, when we call body.replace() all
        # arguments are converted to unicode by python. If there are special
        # chars in the mod_value then we end up with an UnicodeDecodeError, so
        # I convert it myself with some error handling
        #
        # https://github.com/andresriancho/w3af/issues/8953
        mod_value = smart_unicode(mod_value, errors=PERCENT_ENCODE)

        empty = u''
        unquoted = urllib.unquote_plus(mod_value)
        cgi_escape = cgi.escape

        body = body.replace(mod_value, empty)
        body = body.replace(unquoted, empty)
        body = body.replace(cgi_escape(mod_value), empty)
        body = body.replace(cgi_escape(unquoted), empty)

    return body


def get_socket_exception_reason(error):
    """
    :param error: The socket.error exception instance
    :return: The reason/message associated with that exception
    """
    if not isinstance(error, socket.error):
        return

    if error[0] in KNOWN_SOCKET_ERRORS:
        return str(error)

    return


def get_exception_reason(error):
    """
    :param error: The exception instance
    :return: The reason/message associated with that exception (if known)
             else we return None.
    """
    if isinstance(error, URLTimeoutError):
        # New exception type raised by keepalive handler
        return error.message

    # Exceptions may be of type httplib.HTTPException or socket.error
    # We're interested on handling them in different ways
    if isinstance(error, urllib2.URLError):
        reason_err = error.reason

        if isinstance(reason_err, socket.error):
            return get_socket_exception_reason(error)

    if isinstance(error, OpenSSL.SSL.SysCallError):
        if error[0] in KNOWN_SOCKET_ERRORS:
            return str(error[1])

    if isinstance(error, (ssl.SSLError, socket.sslerror)):
        socket_reason = get_socket_exception_reason(error)
        if socket_reason:
            return 'SSL Error: %s' % socket_reason

    if isinstance(error, socket.error):
        return get_socket_exception_reason(error)

    if isinstance(error, HTTPRequestException):
        return error.value

    if isinstance(error, httplib.BadStatusLine):
        return 'Bad HTTP response status line: %s' % error.line

    if isinstance(error, httplib.HTTPException):
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
        return '%s: %s' % (error.__class__.__name__, error.args)

    # Unknown reason
    return None