# -*- coding: utf8 -*-

'''
python_export.py

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

from core.data.parsers.httpRequestParser import httpRequestParser
import re


def python_escape_string( str_in ):
    str_out = str_in.replace('"', '\\"')
    return str_out


def python_export( request_string ):
    '''
    @parameter request_string: The string of the request to export
    @return: A urllib2 based python script that will perform the same HTTP request.
    '''
    # get the header and the body
    splitted_request = request_string.split('\n\n')
    header = splitted_request[0]
    body = '\n\n'.join(splitted_request[1:])
    
    http_request = httpRequestParser( header, body)
    
    # Now I do the real magic...
    res = 'import urllib2\n\n'
    
    res += 'url = "' + python_escape_string(http_request.getURI()) + '"\n'
    
    if http_request.getData() != '\n' and http_request.getData() is not None:
        escaped_data = python_escape_string(str(http_request.getData()) )
        res += 'data = "' + escaped_data + '"\n'
    else:
        res += 'data = None\n'
        
    res += 'headers = { \n'
    headers = http_request.getHeaders()
    for header_name in headers:
        header_value = python_escape_string(headers[header_name])
        header_name = python_escape_string(header_name)        
        res += '\t"' + header_name + '" : "' + header_value + '",\n'
        
    res = res [:-2]
    res += '\n}\n'

    res += '''
request = urllib2.Request(url, data, headers)
response = urllib2.urlopen(request)
response_body = response.read()
'''
    res += 'print response_body\n'

    return res
