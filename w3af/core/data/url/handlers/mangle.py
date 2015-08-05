"""
mangle.py

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

"""
import urllib2

from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.url.handlers.keepalive import HTTPResponse as kaHTTPResponse
from w3af.core.data.url.handlers.output_manager import OutputManagerHandler


class MangleHandler(urllib2.BaseHandler):
    """
    Call mangle plugins for each request and response.
    """

    handler_order = OutputManagerHandler.handler_order - 2

    def __init__(self, plugin_list):
        self._plugin_list = plugin_list

    def http_request(self, request):
        if not self._plugin_list:
            return request

        for plugin in self._plugin_list:
            request = plugin.mangle_request(request)

        return request

    def http_response(self, request, response):
        if not self._plugin_list:
            return response

        # Create the HTTPResponse object
        http_resp = HTTPResponse.from_httplib_resp(response)

        for plugin in self._plugin_list:
            plugin.mangle_response(http_resp)

        response = self._http_resp_2_httplib(response, http_resp)

        return response

    def _http_resp_2_httplib(self, original_response, mangled_response):
        """
        Convert an HTTPResponse.HTTPResponse object to a httplib.httpresponse
        subclass that I created in keepalive.

        :param original_response: HTTPResponse.HTTPResponse object
        :return: httplib.httpresponse subclass
        """
        ka_resp = MangledKeepAliveHTTPResponse()

        ka_resp.set_body(mangled_response.get_body())
        ka_resp.headers = mangled_response.get_headers()
        ka_resp.code = mangled_response.get_code()
        ka_resp._url = mangled_response.get_uri().url_string
        ka_resp.msg = original_response.msg
        ka_resp.id = original_response.id
        ka_resp.set_wait_time(original_response.get_wait_time())
        ka_resp.encoding = mangled_response.charset

        return ka_resp

    https_request = http_request
    https_response = http_response


class MangledKeepAliveHTTPResponse(kaHTTPResponse):
    def __init__(self):
        """
        Overriding in order to allow me to create a response without a socket
        instance. At this point I've already read everything I needed from the
        socket, so it doesn't make any sense to keep a pointer to it.

        :see: https://github.com/andresriancho/w3af/issues/2172
        """
        self._rbuf = ''
        self._method = None

    def close(self):
        """
        Since this HTTP response doesn't have a socket, there is nothing to
        close. We just "pass" to avoid issues like

            https://github.com/andresriancho/w3af/issues/11822

        :return: None
        """
        pass

    def close_connection(self):
        """
        Since this HTTP response doesn't have a socket, there is nothing to
        close. We just "pass" to avoid issues like

            https://github.com/andresriancho/w3af/issues/11822

        :return: None
        """
        pass