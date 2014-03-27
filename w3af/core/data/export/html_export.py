# -*- coding: utf8 -*-

"""
html_export.py

Copyright 2009 Andres Riancho

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

from w3af.core.data.parsers.HTTPRequestParser import HTTPRequestParser


def html_export(request_string):
    """
    :param request_string: The string of the request to export
    :return: A HTML that will perform the same HTTP request.
    """
    request_lines = request_string.split('\n\n')
    header = request_lines[0]
    body = '\n\n'.join(request_lines[1:])
    http_request = HTTPRequestParser(header, body)
    res = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
    <html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <title>Exported HTTP Request from w3af</title>
    </head>
    <body>\n"""
    res += '<form action="' + cgi.escape(http_request.get_uri()
                                         .url_string, True)
    res += '" method="' + cgi.escape(http_request.get_method(), True) + '">\n'
    if http_request.get_data() and http_request.get_data() != '\n':
        post_data = http_request.get_dc()
        for param_name in post_data:
            for value in post_data[param_name]:
                res += '<label>' + cgi.escape(param_name) + '</label>\n'
                res += '<input type="text" name="' + \
                    cgi.escape(param_name.strip(), True)
                res += '" value="' + cgi.escape(value, True) + '">\n'
    res += '<input type="submit">\n'
    res += '</form>\n'
    res += """</body>\n</html>"""
    return res
