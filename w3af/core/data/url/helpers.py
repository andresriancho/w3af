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
import ssl
import copy
import socket
import urllib
import urllib2
import httplib
import OpenSSL
import string

from collections import OrderedDict
from w3af.core.controllers.misc.itertools_toolset import unique_everseen
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

#
# The number of encodings a developer can use is huge, and the frameworks
# don't help either, since some will (for example) write &#034; and other
# will write &#34;
#
# We want to make a real effort to cleanup all the bodies, so we are compiling
# A list with all the ways a special character can be written, and then we
# run all combinations to find the right one used in this page.
#
# Warning! The order in this table is not random! The first items are the ones
# that appear in the escapes of the rest of the characters.
ESCAPE_TABLE = OrderedDict([
    ('#', ['#',                                             '%23', '%2523']),
    ('&', ['&', '&amp;',  '&#x26;', '&#38;', '&#038;']),
    ('%', ['%',                                             '%25', '%2525']),
    ('"', ['"', '&quot;', '&#x22;', '&#34;', '&#034;',                      '\\u0022', '\\"']),
    ("'", ["'", '&apos;', '&#x27;', '&#39;', '&#039;',                      '\\u0027', "\\'"]),
    ('>', ['>', '&gt;',   '&#x3e;', '&#62;', '&#062;']),
    ('=', ['=', '&eq;',   '&#x3d;', '&#61;', '&#061;',      '%3d', '%253d']),
    (' ', [' ', '&nbsp;', '&#x20;', '&#32;', '&#032;', '+', '%20', '%2520']),
    ('<', ['<', '&lt;',   '&#x3c;', '&#60;', '&#060;']),
    (';', [';',                                             '%3b', '%253b']),
    ('/', ['/',                                             '%2f', '%252f']),
    (':', [':',                                             '%3a', '%253a']),
    ('@', ['@',                                             '%40', '%2540']),
    ('$', ['$',                                             '%24', '%2524']),
    (',', [',',                                             '%2c', '%252c']),
    ('?', ['?',                                             '%3f', '%253f']),
])


def extend_escape_table_with_uppercase(escape_table):
    """
    Some ugly sites use &AMP; instead of &amp; and browsers support it.
    Same thing with %3D and %3d

    Since I don't want to make the ESCAPE_TABLE uglier with all the
    upper case versions, I just extend it with this function.

    :return: An extended table with uppercase
    """
    extended_table = copy.deepcopy(escape_table)

    for char, escapes in escape_table.iteritems():
        for escape in escapes:
            upper_case_escape = escape.upper()

            # Ignore those X in the HTML escape
            if escape.startswith('&#x'):
                upper_case_escape = upper_case_escape.replace('&#X', '&#x')

            if upper_case_escape != escape:
                extended_table[char].append(upper_case_escape)

    return extended_table


def extend_escape_table_with_printable_chars(escape_table):
    """
    Some ugly sites will output %41 when we send A, or even A when
    we send "a"

    Since I don't want to manually write a table with all those
    characters I'm going to extend the original with string.printable

    :return: An extended table with uppercase
    """
    extended_table = copy.deepcopy(escape_table)

    for char in string.printable:
        if char not in extended_table:

            dec_val = ord(char)
            hex_val = format(dec_val, 'x')

            char_encodings = ['%' + hex_val,
                              '%25' + hex_val,
                              '&#x%s;' % hex_val,
                              '&#%s;' % dec_val,
                              '&#0%s;' % dec_val]
            extended_table[char] = char_encodings

    return extended_table

# TODO: This can NOT be done! If you enable this line and call the
#       get_clean_body function it will try too many combinations of
#       encodings and use 100% CPU for a very long time.
#
# EXTENDED_TABLE = extend_escape_table_with_printable_chars(ESCAPE_TABLE)

EXTENDED_TABLE = extend_escape_table_with_uppercase(ESCAPE_TABLE)


def apply_multi_escape_table(_input, escape_table=ESCAPE_TABLE):
    inner_iter = _multi_escape_table_impl(_input,
                                          escape_table=escape_table)
    for x in unique_everseen(inner_iter):
        yield x


def _multi_escape_table_impl(_input, escape_table=ESCAPE_TABLE):
    """
    Replace all combinations in the escape table.

    :param _input: The string with special characters
    :param escape_table: The table used to find the special chars
    :return: A string generator with all special characters replaced
    """
    yield _input

    for table_char, escapes in escape_table.iteritems():

        if table_char in _input:
            for escape in escapes:
                modified = _input.replace(table_char, escape)

                # On the first call, and based on the way the table was created,
                # this will yield the unmodified input string
                yield modified

                # This makes the recursion end
                new_escape_table = escape_table.copy()
                new_escape_table.pop(table_char)

                # These lines are here to avoid double and triple encoding
                for char in escape:
                    new_escape_table.pop(char, None)

                inner_generator = _multi_escape_table_impl(modified,
                                                           escape_table=new_escape_table)

                for modified in inner_generator:
                    yield modified


def get_clean_body(mutant, response):
    """
    @see: Very similar to fingerprint_404.py get_clean_body() bug not quite
          the same maybe in the future I can merge both?

    Definition of clean in this method:
        - input:
            - response.get_url() == http://host.tld/aaaaaaa/?id=1 OR 23=23
            - response.get_body() == '...<x>1 OR 23=23</x>...'

        - output:
            - self._clean_body(response) == '...<x></x>...'

    All injected values are removed encoded and 'as is'.

    :param mutant: The mutant where I can get the value from.
    :param response: The HTTPResponse object to clean
    :return: A string that represents the 'cleaned' response body.
    """
    if not response.is_text_or_html():
        return response.body

    body = response.body
    mod_value_1 = mutant.get_token_value()

    # Since the body is already in unicode, when we call body.replace() all
    # arguments are converted to unicode by python. If there are special
    # chars in the mod_value then we end up with an UnicodeDecodeError, so
    # I convert it myself with some error handling
    #
    # https://github.com/andresriancho/w3af/issues/8953
    mod_value_1 = smart_unicode(mod_value_1, errors=PERCENT_ENCODE)

    # unquote, just in case the plugin did an extra encoding of some type.
    # what we want to do here is get the original version of the string
    mod_value_2 = urllib.unquote_plus(mod_value_1)

    payloads_to_replace = set()
    payloads_to_replace.add(mod_value_1)
    payloads_to_replace.add(mod_value_2)

    encoded_payloads = set()

    for payload in payloads_to_replace:
        for encoded_payload in apply_multi_escape_table(payload,
                                                        EXTENDED_TABLE):
            encoded_payloads.add(encoded_payload)

    # uniq sorted by longest len
    encoded_payloads = list(encoded_payloads)
    encoded_payloads.sort(lambda x, y: cmp(len(y), len(x)))

    empty = u''
    replace = unicode.replace
    for to_replace in encoded_payloads:
        body = replace(body, to_replace, empty)

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
        return str(error)

    # Exceptions may be of type httplib.HTTPException or socket.error
    # We're interested on handling them in different ways
    if isinstance(error, urllib2.URLError):
        reason_err = error.reason

        if isinstance(reason_err, socket.error):
            return get_socket_exception_reason(error)

    if isinstance(error, OpenSSL.SSL.SysCallError):
        if error[0] in KNOWN_SOCKET_ERRORS:
            return str(error[1])

    if isinstance(error, OpenSSL.SSL.ZeroReturnError):
        return 'OpenSSL Error: OpenSSL.SSL.ZeroReturnError'

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