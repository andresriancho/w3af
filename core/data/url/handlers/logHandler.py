'''
logHandler.py

Copyright 2006 Andres Riancho

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

import urllib2
import core.controllers.outputManager as om
import core.data.request.fuzzableRequest as fuzzableRequest
import core.data.url.httpResponse as httpResponse

class logHandler(urllib2.BaseHandler):
    """
    Track HTTP requests and responses.
    """
    
    handler_order = urllib2.HTTPErrorProcessor.handler_order -1
    
    def __init__(self):
        pass

    def http_request(self, request):
        if not request.has_header('Host'):
            request.add_unredirected_header('Host', request.host )
            
        if not request.has_header('Accept-Encoding'):
            request.add_unredirected_header('Accept-Encoding', 'identity' )
        
        return request

    def http_response(self, request, response):
        fr = fuzzableRequest.fuzzableRequest()
        fr.setURI( request.get_full_url() )
        fr.setMethod( request.get_method() )
        
        headers = request.headers
        for i in request.unredirected_hdrs.keys():
            headers[ i ] = request.unredirected_hdrs[ i ]
        fr.setHeaders( headers )
        
        if request.get_data() == None:
            fr.setData( '' )
        else:
            fr.setData( request.get_data() )
        
        code, msg, hdrs = response.code, response.msg, response.info()
        url = response.geturl()
        body = response.read()
        id = response.id
        res = httpResponse.httpResponse( code, body, hdrs, url, url, msg=msg, id=id)

        om.out.logHttp( fr, res )
        
        return response

    https_request = http_request
    https_response = http_response

