"""
http_request_parser.py

Copyright 2008 Andres Riancho

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
import urlparse

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.controllers.exceptions import BaseFrameworkException


SUPPORTED_VERSIONS = {'1.0', '1.1'}


def check_version_syntax(version):
    """
    :return: True if the syntax of the version section of HTTP is valid; else
             raise an exception.
    """
    split_version = version.split('/')

    if len(split_version) != 2:
        msg = 'The HTTP request has an invalid version token: "%s"'
        raise BaseFrameworkException(msg % version)

    elif len(split_version) == 2:

        if split_version[0].lower() != 'http':
            msg = ('The HTTP request has an invalid HTTP token in the version'
                   ' specification: "%s"')
            raise BaseFrameworkException(msg % version)

        if split_version[1] not in SUPPORTED_VERSIONS:
            fmt = 'HTTP request version "%s" is unsupported'
            raise BaseFrameworkException(fmt % version)

    return True


def check_uri_syntax(uri, host=None):
    """
    :return: True if the syntax of the URI section of HTTP is valid; else
             raise an exception.
    """
    supported_schemes = ['http', 'https']
    scheme, domain, path, params, qs, fragment = urlparse.urlparse(uri)
    scheme = scheme.lower()

    if not scheme:
        scheme = 'http'
    if not domain:
        domain = host
    if not path:
        path = '/'

    if scheme not in supported_schemes or not domain:
        msg = 'You have to specify the complete URI, including the protocol'
        msg += ' and the host. Invalid URI: %s.'
        raise BaseFrameworkException(msg % uri)

    res = urlparse.urlunparse((scheme, domain, path, params, qs, fragment))
    return res


def raw_http_request_parser(raw_http_request):
    """
    :param raw_http_request: An HTTP request with headers and body as a string
    :return: A FuzzableRequest object with all the corresponding information
             that was sent in head and postdata
    """
    head, postdata = raw_http_request.split('\r\n\r\n', 1)
    return http_request_parser(head, postdata)


def http_request_parser(head, postdata):
    """
    This function parses HTTP Requests from a string to a FuzzableRequest.

    :param head: The head of the request.
    :param postdata: The post data of the request
    :return: A FuzzableRequest object with all the corresponding information
             that was sent in head and postdata

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    # Parse the request head, the strip() helps us deal with the \r (if any)
    split_head = head.split('\n')
    split_head = [h.strip() for h in split_head if h]

    if not split_head:
        msg = 'The HTTP request is invalid.'
        raise BaseFrameworkException(msg)

    # Get method, uri, version
    method_uri_version = split_head[0]
    first_line = method_uri_version.split(' ')
    if len(first_line) == 3:
        # Ok, we have something like "GET /foo HTTP/1.0". This is the best case
        # for us!
        method, uri, version = first_line

    elif len(first_line) < 3:
        msg = 'The HTTP request has an invalid <method> <uri> <version>: "%s"'
        raise BaseFrameworkException(msg % method_uri_version)

    elif len(first_line) > 3:
        # GET /hello world.html HTTP/1.0
        # Mostly because we are permissive... we are going to try to parse
        # the request...
        method = first_line[0]
        version = first_line[-1]
        uri = ' '.join(first_line[1:-1])

    check_version_syntax(version)

    # If we got here, we have a nice method, uri, version first line
    # Now we parse the headers (easy!) and finally we send the request
    headers_str = split_head[1:]
    headers_inst = Headers()

    for header in headers_str:
        one_split_header = header.split(':', 1)
        if len(one_split_header) == 1:
            msg = ('The HTTP request has an invalid header which does not'
                   ' contain the ":" separator: "%s"')
            raise BaseFrameworkException(msg % header)

        header_name = one_split_header[0].strip()
        header_value = one_split_header[1].strip()

        if header_name in headers_inst:
            # Handle duplicated headers
            headers_inst[header_name] += ', ' + header_value
        else:
            headers_inst[header_name] = header_value

    host, _ = headers_inst.iget('host', None)
    
    try:
        uri = URL(check_uri_syntax(uri, host))
    except ValueError, ve:
        raise BaseFrameworkException(str(ve))

    return FuzzableRequest.from_parts(uri, method, postdata, headers_inst)
