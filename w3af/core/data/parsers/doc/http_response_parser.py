"""
http_response_parser.py

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
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.doc.http_request_parser import check_version_syntax
from w3af.core.data.dc.headers import Headers
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.controllers.exceptions import BaseFrameworkException

SUPPORTED_VERSIONS = {'1.0', '1.1'}


def raw_http_response_parser(raw_http_response):
    """
    :param raw_http_response: An HTTP response with headers and body as a string
    :return: An HTTPResponse object with all the corresponding information
             that was sent in headers and post-data
    """
    head, postdata = raw_http_response.split('\r\n\r\n', 1)
    return http_response_parser(head, postdata)


def http_response_parser(head, postdata):
    """
    This function parses HTTP Responses from a string to an HTTPResponse object.

    :param head: The head of the response
    :param postdata: The post data of the response
    :return: An HTTPResponse object with all the corresponding information
             that was sent in headers and post-data
    """
    # Parse the request head, the strip() helps us deal with the \r (if any)
    split_head = head.split('\n')
    split_head = [h.strip() for h in split_head if h]

    if not split_head:
        msg = 'The HTTP response is invalid.'
        raise BaseFrameworkException(msg)

    # Get version code message
    version_code_message = split_head[0]
    first_line = version_code_message.split(' ', 2)

    if len(first_line) == 3:
        # We have something like "HTTP/1.1 200 OK"
        version, code, message = first_line

    elif len(first_line) == 2:
        # We have something like "HTTP/1.1 503"
        version, code = first_line
        message = ''

    else:
        msg = 'The HTTP request has an invalid <version> <code> <message>: "%s"'
        raise BaseFrameworkException(msg % version_code_message)

    try:
        code = int(code)
    except ValueError:
        raise BaseFrameworkException('Invalid HTTP response code %s' % code)

    check_version_syntax(version)

    # If we got here, we have a nice version code message first line
    # Now we parse the headers (easy!) and finally we create the response
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

    dummy_url = URL('http://w3af.com')

    return HTTPResponse(code, postdata, headers_inst, dummy_url, dummy_url)
