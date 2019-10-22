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
import socket
import urllib
import urllib2
import httplib
import OpenSSL
import itertools

from w3af.core.controllers.misc.itertools_toolset import unique_everseen_hash
from errno import (ECONNREFUSED, EHOSTUNREACH, ECONNRESET, ENETDOWN,
                   ENETUNREACH, ETIMEDOUT, ENOSPC)

from w3af.core.data.misc.encoding import smart_unicode, PERCENT_ENCODE
from w3af.core.controllers.exceptions import HTTPRequestException
from w3af.core.data.url.handlers.keepalive import URLTimeoutError
from w3af.core.data.constants.response_codes import NO_CONTENT
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.misc.web_encodings import (URL_ENCODING_FUNCTIONS,
                                               HTML_ENCODING_FUNCTIONS,
                                               JSON_ENCODING_FUNCTIONS,
                                               generate_html_encoding_functions,
                                               generate_url_encoding_functions)

from w3af.core.controllers.misc.number_generator import consecutive_number_generator

# Known reason errors. See errno module for more info on these errors
EUNKNSERV = -2        # Name or service not known error
EINVHOSTNAME = -5     # No address associated with hostname
EUNEXPECTEDEOF = -1   # https://github.com/andresriancho/w3af/issues/10290

KNOWN_SOCKET_ERRORS = (EUNKNSERV, ECONNREFUSED, EHOSTUNREACH, ECONNRESET,
                       ENETDOWN, ENETUNREACH, EINVHOSTNAME, ETIMEDOUT,
                       ENOSPC, EUNEXPECTEDEOF)

NO_CONTENT_MSG = 'No Content'


def new_no_content_resp(uri, add_id=False):
    """
    Return a new NO_CONTENT HTTPResponse object.
    
    :param uri: URI string or request object
    :param add_id: Add ID to the HTTP response
    """
    #
    # WARNING: You are about to change this code? Please read the related
    #          race condition in this commit [0]
    #
    # [0] https://github.com/andresriancho/w3af/commit/682bc2e4ad7d075bbdc469bc5d24a28e6d2e7804
    #
    no_content_response = HTTPResponse(code=NO_CONTENT,
                                       read='',
                                       headers=Headers(),
                                       geturl=uri,
                                       original_url=uri,
                                       msg=NO_CONTENT_MSG)

    if add_id:
        no_content_response.id = consecutive_number_generator.inc()

    return no_content_response


def is_no_content_response(http_response):
    if http_response.get_code() != NO_CONTENT:
        return False

    if http_response.get_msg() != NO_CONTENT_MSG:
        return False

    if http_response.get_headers() != Headers():
        return False

    return True


def apply_multi_escape_table(_input, max_len=None, max_count=None):
    """

    :param _input: The input string which must be escaped using N ways

    :param max_len: The max length of the escaped string that can be returned
                    For example, if max_len is 4, _input is "a&", then
                    "a&amp;" (len: 6) will NOT be in the output but
                    "a%26" (len 4) will. This is usually used for performance
                    improvements.

    :param max_count: The max amount of escapes to generate.

                      This limitation was imposed after seeing that in some cases,
                      like calling get_clean_body() with a mutant that sent a binary
                      file to the HTTP server, the apply_multi_escape_table took
                      more than 1800 seconds to run and generated thousands of
                      escaped strings. Those strings are (most likely) never
                      going to be found in the response.

    :return: Yield escaped versions of _input
    """
    returned = 0

    inner_iter = _multi_escape_table_impl(_input)

    for escaped_input in unique_everseen_hash(inner_iter):

        # Filter output by max_len
        if max_len is not None:
            if len(escaped_input) > max_len:
                continue

        if max_count is not None:
            if max_count <= returned:
                break

        returned += 1
        yield escaped_input


def _multi_escape_table_impl(_input):
    """
    Apply the following functions to the _input and yield results:
        URL_ENCODING_FUNCTIONS
        HTML_ENCODING_FUNCTIONS
        MODIFICATION_FUNCTIONS
        JSON_ENCODING_FUNCTIONS

    In some cases we apply N functions to the _input, for example:
        * Apply one url encoding function
        * Then apply one HTML encoding function
        * Finally apply a modification function and return the result

    And in some other cases we might apply a function of the same class twice:
        * Apply one url encoding function
        * Apply other url encoding function and return the result

    The most commonly used combinations are yield first, this means that
    URL-encoded result comes before *double* URL-decoded result.

    The original string is returned as the first result

    This function doesn't care about yielding unique results since
    apply_multi_escape_table is filtering that for us.

    :param _input: The string with special characters
    :return: A string generator with all special characters replaced
    """
    if not HTML_ENCODING_FUNCTIONS:
        generate_html_encoding_functions()
        generate_url_encoding_functions()

    yield _input

    for encode in itertools.chain(URL_ENCODING_FUNCTIONS,
                                  HTML_ENCODING_FUNCTIONS,
                                  JSON_ENCODING_FUNCTIONS):
        encoded_input = encode(_input)
        if encoded_input != _input:
            yield encoded_input

    # Double URL-encoding
    for encode_1 in URL_ENCODING_FUNCTIONS:
        for encode_2 in URL_ENCODING_FUNCTIONS:
            encoded_input = encode_1(encode_2(_input))
            if encoded_input != _input:
                yield encoded_input

    # URL-encoding and HTML-encoding
    for encode_1 in URL_ENCODING_FUNCTIONS:
        for encode_2 in HTML_ENCODING_FUNCTIONS:
            encoded_input = encode_1(encode_2(_input))
            if encoded_input != _input:
                yield encoded_input

    # HTML-encoding and URL-encoding
    for encode_1 in URL_ENCODING_FUNCTIONS:
        for encode_2 in HTML_ENCODING_FUNCTIONS:
            encoded_input = encode_1(encode_2(_input))
            if encoded_input != _input:
                yield encoded_input

    # Double HTML-encoding doesn't make any sense to me
    # skipping that combination


def get_clean_body(mutant, response, max_escape_count=500):
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

    :param max_escape_count: The max number of escapes to try to replace, note
                             that the default here is 500, which is a little bit
                             more than the max number of escapes generated in the
                             worse case I could imagine at test_apply_multi_escape_table_count
                             which generated ~350.

                             The goal is to make sure that everything is generated
                             but at the same time control any edge cases which I might
                             have missed.

    :return: A string that represents the 'cleaned' response body.
    """
    if not response.is_text_or_html():
        return response.body

    strings_to_replace_list = [mutant.get_token_value()]
    return get_clean_body_impl(response.body,
                               strings_to_replace_list,
                               max_escape_count=max_escape_count)


def get_clean_body_impl(body, strings_to_replace_list, multi_encode=True,
                        max_escape_count=None):
    """
    This is a low level function which allows me to use all the improvements
    I did in the helpers.get_clean_body() in fingerprint_404.get_clean_body().

    Both helpers.get_clean_body() and fingerprint_404.get_clean_body() receive
    different parameters, do some preparation work, and then call this function
    to really do the replacements.

    :param body: HTTP response body
    :param strings_to_replace_list: A list of strings to replace. These can be
                                    byte strings or unicode, we'll handle both
                                    internally.
    :param multi_encode: Apply the multiple encodings before replacing, setting
                         this to True with many strings to replace in the list
                         will consume considerable CPU time.
    :param max_escape_count: The max number of escapes to try to replace, note
                             that the default here is 500, which is a little bit
                             more than the max number of escapes generated in the
                             worse case I could imagine at test_apply_multi_escape_table_count
                             which generated ~350.

                             The goal is to make sure that everything is generated
                             but at the same time control any edge cases which I might
                             have missed.
    :return: The body as a unicode with all strings to replace removed.
    """
    body_lower = body.lower()
    body_len = len(body)
    unicodes_to_replace_set = set()

    for str_to_repl in strings_to_replace_list:

        # Since the body is already in unicode, when we call body.replace() all
        # arguments are converted to unicode by python. If there are special
        # chars in the mod_value then we end up with an UnicodeDecodeError, so
        # I convert it myself with some error handling
        #
        # https://github.com/andresriancho/w3af/issues/8953
        unicode_to_repl = smart_unicode(str_to_repl, errors=PERCENT_ENCODE)

        # unquote, just in case the plugin did an extra encoding of some type.
        # what we want to do here is get the original version of the string
        unicode_to_repl_unquoted = urllib.unquote_plus(unicode_to_repl)

        unicodes_to_replace_set.add(unicode_to_repl)
        unicodes_to_replace_set.add(unicode_to_repl_unquoted)

    # Now we apply multiple encodings to find in different responses
    encoded_payloads = set()

    if multi_encode:
        # Populate the set with multiple versions of the same set
        for unicode_to_repl in unicodes_to_replace_set:

            # If the unicode_to_repl (in its original version, without applying
            # the multi escape table) is larger than the response body; and
            # taking into account that `apply_multi_escape_table` will always
            # return a string which is equal or larger than the original; we
            # reduce the CPU-usage of this function by preventing the generation
            # of strings which will NEVER be replaced in:
            #
            #   body = replace(body, to_replace, empty)
            #
            # Because to_replace will be larger than body: ergo, it will never
            # be there.
            if len(unicode_to_repl) > body_len:
                continue

            # Note that we also do something similar with the max_len=body_len
            # parameter we send to apply_multi_escape_table
            for encoded_to_repl in apply_multi_escape_table(unicode_to_repl,
                                                            max_len=body_len,
                                                            max_count=max_escape_count):
                encoded_payloads.add(encoded_to_repl)
    else:
        # Just leave the the two we have
        encoded_payloads = unicodes_to_replace_set

    # uniq sorted by longest len
    encoded_payloads = list(encoded_payloads)
    encoded_payloads.sort(lambda x, y: cmp(len(y), len(x)))
    encoded_payloads = [i.lower() for i in encoded_payloads]

    for to_replace in encoded_payloads:
        body, body_lower = remove_using_lower_case(body, body_lower, to_replace)

    return body


def remove_using_lower_case(body, body_lower, to_replace):
    """
    Replace `to_replace` (which will always be lower case) in `body`
    (which is the original string) using `body_lower` as base for the
    search.

    Example input:
        body: Hello World World
        body_lower: hello world world
        to_replace: world

    Output:
        body: Hello
        body_lower: hello

    :param body: The original string
    :param body_lower: The original string after .lower()
    :param to_replace: The string to replace
    :return: A tuple containing:
                The original string without `to_replace`
                The string from the first item after .lower()
    """
    idx = 0
    to_replace_len = len(to_replace)

    while idx < len(body):
        index_l = body_lower.find(to_replace, idx)

        if index_l == -1:
            return body, body_lower

        body = body[:index_l] + body[index_l + to_replace_len:]
        body_lower = body.lower()

        idx = index_l + 1

    return body, body_lower


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
