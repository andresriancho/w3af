'''
httpRequestParser.py

Copyright 2008 Andres Riancho

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
import urlparse

from core.data.request.frFactory import createFuzzableRequestRaw
from core.controllers.w3afException import w3afException


def checkVersionSintax(version):
    '''
    @return: True if the sintax of the version section of HTTP is valid; else raise an exception.
    '''
    supportedVersions = ['1.0', '1.1']
    splittedVersion = version.split('/')

    if len(splittedVersion) != 2:
        msg = 'The HTTP request has an invalid version token: "' + version +'"'
        raise w3afException(msg)
    elif len(splittedVersion) == 2:
        if splittedVersion[0].lower() != 'http':
            msg = 'The HTTP request has an invalid HTTP token in the version specification: "'
            msg += version + '"'
            raise w3afException(msg)
        if splittedVersion[1] not in supportedVersions:
            raise w3afException('HTTP request version "' + version + '" is unsupported')
    return True

def checkURISintax(uri, host=None):
    '''
    @return: True if the sintax of the URI section of HTTP is valid; else raise an exception.
    '''
    supportedSchemes = ['http', 'https']
    scheme, domain, path, params, qs, fragment = urlparse.urlparse(uri)

    if not scheme:
        scheme = 'http'
    if not domain:
        domain = host
    if not path:
        path = '/'

    if scheme not in supportedSchemes or not domain:
        msg = 'You have to specify the complete URI, including the protocol and the host.'
        msg += ' Invalid URI: ' + uri
        raise w3afException(msg)

    res = urlparse.urlunparse( (scheme, domain, path, params, qs, fragment) )
    return res

def httpRequestParser(head, postdata):
    '''
    This function parses HTTP Requests from a string to a fuzzableRequest.
    
    @parameter head: The head of the request.
    @parameter postdata: The post data of the request
    @return: A fuzzableRequest object with all the corresponding information that was sent in head and postdata
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    # Parse the request head
    splitted_head = head.split('\n')
    splitted_head = [h.strip() for h in splitted_head if h]
    
    if not splitted_head:
        msg = 'The HTTP request is invalid.'
        raise w3afException(msg)        
    
    # Get method, uri, version
    metUriVer = splitted_head[0]
    firstLine = metUriVer.split(' ')
    if len(firstLine) == 3:
        # Ok, we have something like "GET /foo HTTP/1.0". This is the best case for us!
        method, uri, version = firstLine
    elif len(firstLine) < 3:
        msg = 'The HTTP request has an invalid <method> <uri> <version> token: "'
        msg += metUriVer +'".'
        raise w3afException(msg)
    elif len(firstLine) > 3:
        # GET /hello world.html HTTP/1.0
        # Mostly because we are permissive... we are going to try to send the request...
        method = firstLine[0]
        version = firstLine[-1]
        uri = ' '.join( firstLine[1:-1] )
    
    checkVersionSintax(version)
    
    # If we got here, we have a nice method, uri, version first line
    # Now we parse the headers (easy!) and finally we send the request
    headers = splitted_head[1:]
    headersDict = {}
    for header in headers:
        one_splitted_header = header.split(':', 1)
        if len(one_splitted_header) == 1:
            raise w3afException('The HTTP request has an invalid header: "' + header + '"')
        headersDict[ one_splitted_header[0].strip() ] = one_splitted_header[1].strip()
    host = ''
    for headerName in headersDict:
        if headerName.lower() == 'host':
            host = headersDict[headerName]
    uri = checkURISintax(uri, host)
    fuzzReq = createFuzzableRequestRaw(method, uri, postdata, headersDict)
    return fuzzReq
