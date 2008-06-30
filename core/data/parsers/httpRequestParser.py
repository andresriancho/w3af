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

import core.controllers.outputManager as om
from core.data.request.fuzzableRequest import fuzzableRequest
from core.controllers.w3afException import w3afException

def httpRequestParser(head, postdata):
    '''
    This function parses HTTP Requests from a string to a fuzzableRequest.
    
    @parameter head: The head of the request.
    @parameter postdata: The post data of the request
    @return: A fuzzableRequest object with all the corresponding information that was sent in head and postdata
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def checkVersionSintax( version ):
        splittedVersion = version.split('/')
        if len(splittedVersion) != 2:
            # Invalid!
            raise w3afException('You are trying to send a HTTP request with an invalid version token: ' + version)
        elif len(splittedVersion) == 2:
            if splittedVersion[0].lower() != 'http':
                raise w3afException('You are trying to send a HTTP request with an invalid HTTP token in the version specification: ' + version)
            if splittedVersion[1] not in ['1.0', '1.1']:
                raise w3afException('You are trying to send a HTTP request with a version that is unsupported: ' + version)
        return True
    
    def checkURISintax( uri ):
        if uri.startswith('http://') and len(uri) != len('http://'):
            return True
        elif uri.startswith('https://') and len(uri) != len('https://'):
            return True
        else:
            raise w3afException('You have to specify the complete URI, including the protocol and the host. Invalid URI: ' + uri )
    
    # parse the request head
    splittedHead = head.split('\n')
    splittedHead = [ h.strip() for h in splittedHead if h ]
    
    # Get method, uri, version
    metUriVer = splittedHead[0]
    firstLine = metUriVer.split(' ')
    if len(firstLine) == 3:
        # Ok, we have something like "GET / HTTP/1.0"
        # Or something like "GET /hello+world.html HTTP/1.0"
        # This is the best case for us!
        method, uri, version = firstLine
        checkURISintax(uri)
        checkVersionSintax(version)
    elif len(firstLine) < 3:
        # Invalid!
        raise w3afException('You are trying to send a HTTP request with an invalid <method> <uri> <version> token: ' + metUriVer )
    elif len(firstLine) > 3:
        # This is mostly because the user sent something like this:
        # GET /hello world.html HTTP/1.0
        # Note that the correct sintax is:
        # GET /hello+world.html HTTP/1.0
        # or
        # GET /hello%20world.html HTTP/1.0
        # Mostly because we are permissive... we are going to try to send the request...
        method = firstLine[0]
        version = firstLine[-1]
        checkVersionSintax(version)
        
        # If we get here, it means that we may send the request after all...
        # FIXME: Should I encode here?
        # FIXME: Should the uri be http://host + uri ?
        uri = ' '.join( firstLine[1:-1] )
        checkURISintax(uri)
        
    # If we got here, we have a nice method, uri, version first line
    # Now we parse the headers (easy!) and finally we send the request
    headers = splittedHead[1:]
    headersDict = {}
    for h in headers:
        oneSplittedHeader = h.split(':')
        if len(oneSplittedHeader) == 2:
            headersDict[ oneSplittedHeader[0].strip() ] = oneSplittedHeader[1].strip()
        elif len(oneSplittedHeader) == 1:
            raise w3afException('You are trying to send a HTTP request with an invalid header: ' + h )
        elif len(oneSplittedHeader) > 2:
            headerValue = ' '.join(oneSplittedHeader[1:]).strip()
            headersDict[ oneSplittedHeader[0].strip() ] = headerValue
    
    # And now we create the fuzzableRequest object
    fuzzReq = fuzzableRequest()
    fuzzReq.setURI(uri)
    fuzzReq.setHeaders(headersDict)
    fuzzReq.setMethod(method)
    fuzzReq.setData(postdata) 
    return fuzzReq
