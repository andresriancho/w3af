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

from mitmproxy.controller import Master, handler
from mitmproxy.models import HTTPResponse as MITMProxyHTTPResponse

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.misc.encoding import smart_str, smart_unicode
from w3af.core.controllers.daemons.proxy.templates.utils import render
from w3af.core.controllers.daemons.proxy.empty_handler import EmptyHandler


class ProxyHandler(Master, EmptyHandler):
    """
    All HTTP traffic goes through the `request` method.

    More hooks are available and can be used to intercept/modify HTTP traffic,
    see mitmproxy docs and EmptyHandler for more information.

    http://mitmproxy.org/doc/
    """

    def __init__(self, options, server, uri_opener, parent_process):
        EmptyHandler.__init__(self)
        Master.__init__(self, options, server)

        self.uri_opener = uri_opener
        self.parent_process = parent_process

    @handler
    def request(self, flow):
        """
        This method handles EVERY request that was send by the browser, since
        this is just a base/example implementation we just:

            * Load the request form the flow
            * Translate the request into a w3af HTTPRequest
            * Send it to the wire using our uri_opener
            * Set the response

        :param flow: A mitmproxy flow containing the request
        """
        # This signals mitmproxy that the request will be handled by us
        flow.reply.take()

        self.parent_process.total_handled_requests += 1

        t = threading.Thread(target=self.handle_request_in_thread,
                             args=(flow,),
                             name='ThreadProxyRequestHandler')
        t.daemon = True
        t.start()

    def handle_request_in_thread(self, flow):
        http_request = self._to_w3af_request(flow.request)

        try:
            # Send the request to the remote web server
            http_response = self._send_http_request(http_request)
        except Exception, e:
            trace = str(traceback.format_exc())
            http_response = self._create_error_response(http_request,
                                                        None,
                                                        e,
                                                        trace=trace)

        # This signals mitmproxy that we have a response for this request
        if flow.reply.state == 'taken':
            if not flow.reply.has_message:
                flow.reply.ack()
            flow.reply.commit()

        # Send the response (success|error) to the browser
        http_response = self._to_mitmproxy_response(http_response)
        flow.response = http_response

    def _to_w3af_request(self, mitmproxy_request):
        """
        Convert mitmproxy HTTPRequest to w3af HTTPRequest
        """
        url = '%s://%s:%s%s' % (mitmproxy_request.scheme,
                                mitmproxy_request.host,
                                mitmproxy_request.port,
                                mitmproxy_request.path)

        return HTTPRequest(URL(url),
                           data=mitmproxy_request.content,
                           headers=mitmproxy_request.headers.items(),
                           method=mitmproxy_request.method)

    def _to_mitmproxy_response(self, w3af_response):
        """
        Convert w3af HTTPResponse to mitmproxy HTTPResponse
        """
        header_items = []
        charset = w3af_response.charset
        content_encoding = 'content-encoding'

        body = smart_str(w3af_response.body, charset, errors='ignore')

        for header_name, header_value in w3af_response.headers.items():
            if header_name.lower() == content_encoding:
                continue

            header_name = smart_str(header_name, charset, errors='ignore')
            header_value = smart_str(header_value, charset, errors='ignore')
            header_items.append((header_name, header_value))

        # This is an important step! The ExtendedUrllib will gunzip the body
        # for us, which is great, but we need to change the content-encoding
        # for the response in order to match the decoded body and avoid the
        # HTTP client using the proxy from failing
        header_items.append((content_encoding, 'identity'))

        return MITMProxyHTTPResponse.make(
            status_code=w3af_response.get_code(),
            content=body,
            headers=header_items
        )

    def _send_http_request(self, http_request, grep=True, debugging_id=None):
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
                           debugging_id=debugging_id,

                           #
                           # This is an important one, which needs to be
                           # properly documented.
                           #
                           # What happens here is that mitmproxy receives a
                           # request from xurllib configured to send requests
                           # via a proxy, and then another xurllib with the same
                           # proxy config tries to forward the request.
                           #
                           # Since it has a proxy config it will enter a "proxy
                           # request routing loop" if use_proxy is not set to False
                           #
                           use_proxy=False)

    def _create_error_response(self, request, response, exception, trace=None):
        """

        :param request: The HTTP request which triggered the exception
        :param response: The response (if any) we were processing and triggered
                         the exception
        :param exception: The exception instance
        :return: A mitmproxy response object ready to send to the flow
        """
        context = {'exception_message': exception,
                   'http_request': request.dump(),
                   'traceback': trace.replace('\n', '<br/>\n') if trace else ''}

        for key, value in context.iteritems():
            context[key] = smart_unicode(value, errors='ignore')

        content = render('error.html', context)

        headers = Headers((
            ('Connection', 'close'),
            ('Content-type', 'text/html'),
        ))

        http_response = HTTPResponse(500,
                                     content.encode('utf-8'),
                                     headers,
                                     request.get_uri(),
                                     request.get_uri(),
                                     msg='Server error')
        return http_response
