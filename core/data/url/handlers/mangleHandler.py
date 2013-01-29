'''
mangleHandler.py

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

import core.data.url.HTTPResponse as HTTPResponse

from core.data.request.fuzzable_request import FuzzableRequest
from core.data.url.HTTPRequest import HTTPRequest as HTTPRequest
from core.data.parsers.url import URL
from core.data.url.handlers.keepalive import HTTPResponse as kaHTTPResponse
from core.data.url.handlers.logHandler import LogHandler


class mangleHandler(urllib2.BaseHandler):
    """
    Call mangle plugins for each request and response.
    """

    handler_order = LogHandler.handler_order - 2

    def __init__(self, plugin_list):
        self._plugin_list = plugin_list

    def _urllibReq2fr(self, request):
        '''
        Convert a urllib2 request object to a FuzzableRequest.
        Used in http_request.

        @param request: A urllib2 request obj.
        @return: A FuzzableRequest.
        '''
        headers = request.headers
        headers.update(request.unredirected_hdrs)
        fr = FuzzableRequest(request.url_object,
                             request.get_method(),
                             headers)
        fr.set_data(request.get_data() or '')
        return fr

    def _fr2urllibReq(self, fuzzable_request, orig_req):
        '''
        Convert a FuzzableRequest to a urllib2 request object.
        Used in http_request.

        @param fuzzable_request: A FuzzableRequest.
        @return: A urllib2 request obj.
        '''
        host = fuzzable_request.get_url().get_domain()

        if fuzzable_request.get_method().upper() == 'GET':
            data = None
        else:
            data = fuzzable_request.get_data()

        req = HTTPRequest(
            fuzzable_request.get_uri(), data=data,
            headers=fuzzable_request.get_headers(),
            origin_req_host=host,
            follow_redir=orig_req.follow_redir
        )
        return req

    def http_request(self, request):
        if self._plugin_list:
            fr = self._urllibReq2fr(request)

            for plugin in self._plugin_list:
                fr = plugin.mangle_request(fr)

            request = self._fr2urllibReq(fr, request)
        return request

    def http_response(self, request, response):

        if len(self._plugin_list) and response._connection.sock is not None:
            # Create the HTTPResponse object
            code, msg, hdrs = response.code, response.msg, response.info()
            url_instance = URL(response.geturl())
            body = response.read()
            # Id is not here, the mangle is done BEFORE logging
            # id = response.id

            httpRes = HTTPResponse.HTTPResponse(code, body, hdrs, url_instance,
                                                request.url_object, msg=msg)

            for plugin in self._plugin_list:
                plugin.mangle_response(httpRes)

            response = self._HTTPResponse2httplib(response, httpRes)

        return response

    def _HTTPResponse2httplib(self, originalResponse, mangledResponse):
        '''
        Convert an HTTPResponse.HTTPResponse object to a httplib.httpresponse
        subclass that I created in keepalive.

        @param HTTPResponse: HTTPResponse.HTTPResponse object
        @return: httplib.httpresponse subclass
        '''
        kaRes = kaHTTPResponse(originalResponse._connection.sock, debuglevel=0,
                               strict=0, method=None)
        kaRes.set_body(mangledResponse.get_body())
        kaRes.headers = mangledResponse.get_headers()
        kaRes.code = mangledResponse.get_code()
        kaRes._url = mangledResponse.get_uri().url_string
        kaRes.msg = originalResponse.msg
        kaRes.id = originalResponse.id
        kaRes.encoding = mangledResponse.charset
        return kaRes

    https_request = http_request
    https_response = http_response
