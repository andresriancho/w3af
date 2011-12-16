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

from core.data.request.frFactory import create_fuzzable_request
import core.controllers.outputManager as om
import core.data.url.httpResponse as httpResponse


class LogHandler(urllib2.BaseHandler):
    """
    Add an unique id attribute to http responses and then log them.
    """
    
    handler_order = urllib2.HTTPErrorProcessor.handler_order - 1
        
    def http_request(self, request):
        '''
        perform some ugly hacking of request headers and go on...
        '''
        #
        # FIXME: What if the user doesn't want to add these headers?
        #
        if not request.has_header('Host'):
            request.add_unredirected_header('Host', request.host)
            
        if not request.has_header('Accept-encoding'):
            request.add_unredirected_header('Accept-Encoding', 'identity')
        
        return request
    
    def http_response(self, request, response):
        self.log_req_resp(request, response)
        return response

    https_request = http_request
    https_response = http_response

    @staticmethod
    def log_req_resp(request, response):
        '''
        Send the request and the response to the output manager.
        '''        
        fr = create_fuzzable_request(
                             request, add_headers=request.unredirected_hdrs)
        if isinstance(response, httpResponse.httpResponse):
            resp = response
        else:
            resp = httpResponse.from_httplib_resp(
                                  response, original_url=request.url_object)
            resp.setId(response.id)
        
        om.out.logHttp(fr, resp)