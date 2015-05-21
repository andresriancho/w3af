# -*- coding: utf8 -*-

"""
ruby_export.py

Copyright 2009 Patrick Hof

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
from w3af.core.data.parsers.doc.http_request_parser import http_request_parser


def ruby_escape_string(str_in):
    str_out = str_in.replace('"', '\\"')
    return str_out


def ruby_export(request_string):
    """
    :param request_string: The string of the request to export
    :return: A net/http based ruby script that will perform the same HTTP
             request.
    """
    # get the header and the body
    splitted_request = request_string.split('\n\n')
    header = splitted_request[0]
    body = '\n\n'.join(splitted_request[1:])

    http_request = http_request_parser(header, body)

    # Now I do the real magic...
    res = 'require \'net/https\'\n\n'

    res += 'url = URI.parse("' + ruby_escape_string(
        http_request.get_uri().url_string) + '")\n'

    if http_request.get_data() != '\n' and http_request.get_data():
        escaped_data = ruby_escape_string(str(http_request.get_data()))
        res += 'data = "' + escaped_data + '"\n'
    else:
        res += 'data = nil\n'

    res += 'headers = {\n'
    headers = http_request.get_headers()
    for header_name, header_value in headers.iteritems():
        header_value = ruby_escape_string(header_value)
        header_name = ruby_escape_string(header_name)
        res += '    "' + header_name + '" => "' + header_value + '",\n'

    res = res[:-2]
    res += '\n}\n'

    method = http_request.get_method()
    res += 'res = Net::HTTP.start(url.host, url.port) do |http|\n'
    res += '    http.use_ssl = '
    if http_request.get_url().get_protocol().lower() == 'https':
        res += 'true\n'
    else:
        res += 'false\n'
    res += '    http.send_request("' + method + '", url.path, data, headers)\n'
    res += 'end\n\n'
    res += 'puts res.body\n'

    return res
