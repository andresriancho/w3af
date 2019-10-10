"""
parse_http_log.py

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
from w3af.core.data.parsers.doc.http_request_parser import raw_http_request_parser
from w3af.core.data.parsers.doc.http_response_parser import raw_http_response_parser


REQUEST_START = '=' * 40 + 'Request'
RESPONSE_START = '=' * 40 + 'Response'

REQUEST_END = RESPONSE_START
RESPONSE_END = '=' * 80


def iter_http_request_responses(filename):
    inside_request = False
    inside_response = False

    request_str = ''
    response_str = ''

    _id = 1

    for line in file(filename):
        if line.startswith(REQUEST_START):
            inside_request = True
            continue

        if line.startswith(REQUEST_END):
            inside_request = False
            inside_response = True
            continue

        if line.startswith(RESPONSE_END):
            inside_response = False

            request = raw_http_request_parser(request_str)
            response = raw_http_response_parser(response_str)

            response.set_uri(request.get_uri())
            response.set_id(_id)

            _id += 1

            request_str = ''
            response_str = ''

            yield request, response

            continue

        if inside_request:
            request_str += line

        if inside_response:
            response_str += line
