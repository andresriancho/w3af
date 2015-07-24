"""
handler.py

Copyright 2015 Andres Riancho

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
import threading
import traceback

from netlib.odict import ODictCaseless
from libmproxy.controller import Master
from libmproxy.protocol.http import HTTPResponse as LibMITMProxyHTTPResponse

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.misc.encoding import smart_str
from w3af.core.controllers.daemons.proxy.templates.utils import render


class ProxyHandler(Master):
    """
    All HTTP traffic goes through these (main) methods:

        * handle_request(request libmproxy.http.HTTPRequest) - if we return
          HTTPResponse here then proxy just response to client

        * handle_response(response libmproxy.http.HTTPResponse) - is called
          before sending response to client

        * handle_error(err libmproxy.proxy.primitives.Error)

    More hooks are available and can be used to intercept/modify HTTP traffic,
    see mitmproxy docs for more information.

    http://mitmproxy.org/doc/scripting/libmproxy.html
    http://mitmproxy.org/doc/
    """

    def __init__(self, server, uri_opener, parent_process):
        Master.__init__(self, server)
        self.uri_opener = uri_opener
        self.parent_process = parent_process

    def _to_w3af_request(self, request):
        """
        Convert libmproxy.http.HTTPRequest to
        w3af.core.data.url.HTTPRequest.HTTPRequest
        """
        url = '%s://%s:%s%s' % (request.scheme, request.host,
                                request.port, request.path)

        return HTTPRequest(URL(url),
                           data=request.content,
                           headers=request.headers.items(),
                           method=request.method)

    def _to_libmproxy_response(self, request, response):
        """
        Convert w3af.core.data.url.HTTPResponse.HTTPResponse  to
        libmproxy.http.HTTPResponse
        """
        charset = response.charset

        body = smart_str(response.body, charset, errors='ignore')

        header_items = []
        for header_name, header_value in response.headers.items():
            header_name = smart_str(header_name, charset, errors='ignore')
            header_value = smart_str(header_value, charset, errors='ignore')
            header_items.append((header_name, header_value))

        headers = ODictCaseless(header_items)

        # This is an important step! The ExtendedUrllib will gunzip the body
        # for us, which is great, but we need to change the content-encoding
        # for the response in order to match the decoded body and avoid the
        # HTTP client using the proxy from failing
        headers['content-encoding'] = ['identity']

        return LibMITMProxyHTTPResponse(request.httpversion,
                                        response.get_code(),
                                        str(response.get_msg()),
                                        headers,
                                        body)

    def _send_http_request(self, http_request, grep=True):
        """
        Send a w3af HTTP request to the web server using w3af's HTTP lib

        No error handling is performed, someone else should do that.

        :param http_request: The request to send
        :return: The response
        """
        http_method = getattr(self.uri_opener, http_request.get_method())
        return http_method(http_request.get_uri(),
                           data=http_request.get_data(),
                           headers=http_request.get_headers(),
                           grep=grep,
                           # This is an important one, which needs to be
                           # properly documented. What happens here is that
                           # libmproxy receives a request from xurllib
                           # configured to send requests via proxy, and then
                           # another xurllib with the same proxy config tries
                           # to forward the request. Since it has a proxy config
                           # it will enter a "proxy request routing loop"
                           use_proxy=False)

    def _create_error_response(self, request, response, exception, trace=None):
        """

        :param request: The HTTP request which triggered the exception
        :param response: The response (if any) we were processing and triggered
                         the exception
        :param exception: The exception instance
        :return: A mitmproxy response object ready to send to the flow
        """
        def replace_new_lines(in_str):
            return in_str.replace('\n', '<br/>')

        context = {'exception_message': str(exception),
                   'http_request': request.dump()}

        if trace is not None:
            context['traceback'] = replace_new_lines(trace)

        content = render('error.html', context)

        headers = Headers((
            ('Connection', 'close'),
            ('Content-type', 'text/html'),
        ))

        http_response = HTTPResponse(500, content.encode('utf-8'), headers,
                                     request.get_uri(), request.get_uri(),
                                     msg='Server error')
        return http_response

    def handle_request(self, flow):
        """
        This method handles EVERY request that was send by the browser, we
        decide if the request needs to be trapped and queue it if needed.

        :param flow: A libmproxy flow containing the request
        """
        self.parent_process.total_handled_requests += 1

        t = threading.Thread(target=self.handle_request_in_thread,
                             args=(flow,),
                             name='ThreadProxyRequestHandler')
        t.daemon = True
        t.start()

    def handle_request_in_thread(self, flow):
        """
        This method handles EVERY request that was send by the browser, since
        this is just a base/example implementation we just:

            * Load the request form the flow
            * Translate the request into a w3af HTTPRequest
            * Send it to the wire using our uri_opener
            * Set the response

        :param flow: A libmproxy flow containing the request
        """
        http_request = self._to_w3af_request(flow.request)

        try:
            # Send the request to the remote webserver
            http_response = self._send_http_request(http_request)
        except Exception, e:
            trace = str(traceback.format_exc())
            http_response = self._create_error_response(http_request, None, e,
                                                        trace=trace)

        # Send the response (success|error) to the browser
        http_response = self._to_libmproxy_response(flow.request, http_response)
        flow.reply(http_response)
