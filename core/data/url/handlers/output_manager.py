'''
output_manager.py

Copyright 2006 Andres Riancho

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

'''
import urllib2

import core.controllers.output_manager as om

from core.data.url.HTTPResponse import HTTPResponse
from core.data.url.HTTPRequest import HTTPRequest


class OutputManagerHandler(urllib2.BaseHandler):
    """
    Send the HTTP request and response to the output manager
    """

    handler_order = urllib2.HTTPErrorProcessor.handler_order - 1

    def http_response(self, request, response):
        self.log_req_resp(request, response)

    https_response = http_response

    @staticmethod
    def log_req_resp(request, response):
        '''
        Send the request and the response to the output manager.
        '''
        if not isinstance(response, HTTPResponse):
            url = request.url_object
            resp = HTTPResponse.from_httplib_resp(response,
                                                  original_url=url)
            resp.set_id(response.id)
        else:
            resp = response
            
        if not isinstance(request, HTTPRequest):
            msg = 'There is something odd going on in OutputManagerHandler,'\
                  ' request should be of type HTTPRequest got %s'\
                  ' instead.'
            raise TypeError(msg % type(request))

        om.out.log_http(request, resp)
