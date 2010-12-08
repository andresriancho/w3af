# -*- coding: utf8 -*-

'''
html_export.py

Copyright 2009 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
import urllib
import cgi

import core.data.parsers.urlParser as urlParser
from core.data.parsers.httpRequestParser import httpRequestParser

def html_export(request_string):
    '''
    @parameter request_string: The string of the request to export
    @return: A HTML that will perform the same HTTP request.
    '''
    requestLines = request_string.split('\n\n')
    header = requestLines[0]
    body = '\n\n'.join(requestLines[1:])
    httpRequest = httpRequestParser( header, body)
    res = '''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
    <html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <title>Exported HTTP Request from W3AF</title>
    </head>
    <body>'''
    res += '<form action="' + httpRequest.getURI() +'" method="' + httpRequest.getMethod() + '">\n'
    if httpRequest.getData() and httpRequest.getData() != '\n':
        postData = httpRequest.getDc()
        for i in postData:
            res += '<label>' + i + '</label>\n'
            res += '<input type="text" name="' + i.strip() + '" value="' + postData[i][0] + '">\n'
    res += '<input type="submit">\n'
    res += '</form>\n'
    res += '''</body>\n</html>'''
    return res
