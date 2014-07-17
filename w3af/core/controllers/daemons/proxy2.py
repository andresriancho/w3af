"""
proxy.py

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
import os
import time
import traceback
from multiprocessing.dummy import Process
from BaseHTTPServer import BaseHTTPRequestHandler

from libmproxy import controller
from libmproxy.proxy import server, config
from libmproxy.protocol import http

from w3af import ROOT_PATH
from w3af.core.controllers import output_manager as om
from w3af.core.controllers.exceptions import (ProxyException,
                                              BaseFrameworkException)
from w3af.core.data.dc.headers import Headers
from w3af.core.data.url.HTTPRequest import HTTPRequest
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.parsers.url import URL
from w3af.core.controllers import templates


class w3afProxyHandler(object):
    def __init__(self, master):
        super(w3afProxyHandler, self).__init__()
        self._master = master

    @property
    def uri_opener(self):
        return self._master.uri_opener

    def shutdown(self):
        self._master.shutdown()

    def send_to_server(self, request, grep=False):
        """
        Send a request that arrived from the browser to the remote web server.

        :param request: w3af.core.data.url.HTTPRequest.HTTPRequest
        :param grep: bool
        :rtype : w3af.core.data.url.HTTPResponse.HTTPResponse

        Important variables and methods used here:
            - request.get_headers(): Stores the headers for the request
            - request.data: A file like object that stores the post_data
            - request.get_full_url(): Stores the URL that was requested
                                 by the browser
        """

        uri_instance = URL(request.get_full_url())
        post_data = None
        headers = request.get_headers()
        if headers.iget("Content-Type"):
            # most likely a POST request
            post_data = request.data

        try:
            http_method = getattr(self.uri_opener, request.method)
            res = http_method(uri_instance, data=post_data,
                              headers=headers, grep=grep)
        except BaseFrameworkException, w:
            om.out.error('The proxy request failed, error: ' + str(w))
            raise w
        except Exception, e:
            raise e
        else:
            return res

    def send_error(self, request, exceptionObj, trace=None):
        """
        Send an error to the browser.

        """
        headers = Headers((
            ('Connection', 'close'),
            ('Content-type', 'text/html'),
        ))
        ctx = {"exceptionObj": str(exceptionObj)}
        if trace:
            ctx["trace"] = ('\nTraceback for this error: <br/><br/>'
                            + trace.replace('\n', '<br/>'))
        content = templates.render("proxy/error.html", )
        res = HTTPResponse(400, content.encode("utf-8"), headers,
                           request.get_uri(), request.get_uri(),
                           msg=BaseHTTPRequestHandler.responses[400][0])
        return res

    def handle_request(self, request):
        """
        Handle request from browser, if method returns None then request
        will be proxied through proxy server directly else response will
        be returned to browser

        :rtype : w3af.core.data.url.HTTPResponse.HTTPResponse
        :param request: w3af.core.data.url.HTTPRequest.HTTPRequest
        """
        res = None
        try:
            # Send the request to the remote webserver
            res = self.send_to_server(request)
        except Exception, e:
            res = self.send_error(request, e, trace=str(traceback.format_exc()))
        finally:
            return res


# There is a problem with libmproxy Master implementation.
# It depends on "should_exit" global variable.
# So, right now we can't create multiple master implementations and Proxy.
# The solution is to make pull request to libmproxy with master without
# global variable dependency.
class Master(controller.Master):
    """
    All communications with HTTP handler passes through messages.

    Available handlers:

    ask  - wait for reply from handler through arg.reply method
    tell - proxy send and forget about these handlers

    tell handle_serverconnect(server_connection
         libmproxy.proxy.server.ConnectionHandler) - is called right before
         server connection established
    tell handle_serverdisconnect(server_connection
         libmproxy.proxy.server.ConnectionHandler) - is called right before
         server disconnect


    tell handle_clientconnect(client_connection
         libmproxy.proxy.server.ConnectionHandler) - is called before
         handle_request
    tell handle_clientdisconnect(client_connection
         libmproxy.proxy.server.ConnectionHandler)

    tell handle_log(log libmproxy.proxy.primitives.Log)
    ask  handle_error(err libmproxy.proxy.primitives.Error)

    // these are for http requests:
    ask  handle_request(request libmproxy.http.HTTPRequest) - if we return
         HTTPResponse here then proxy just response to client
    ask  handle_response(response libmproxy.http.HTTPResponse) - is called
         before sending response to client
    """

    def __init__(self, server, uri_opener, handler=w3afProxyHandler):
        controller.Master.__init__(self, server)
        self.uri_opener = uri_opener
        self.handler_class = handler

    def _convert_request(self, request):
        """Convert limproxy.http.HTTPRequest to
        w3af.core.data.url.HTTPRequest.HTTPRequest
        """
        return HTTPRequest(URL(request.get_url()), request.content,
                           request.headers.items(), request.get_host(),
                           method=request.method)

    def _convert_response(self, res, request):
        """Convert w3af.core.data.url.HTTPResponse.HTTPResponse  to
        limproxy.http.HTTPResponse
        """
        return http.HTTPResponse(request.httpversion, res.get_code(),
                                 res.get_msg(),
                                 http.ODictCaseless(res.headers.items()),
                                 res.body)

    def handle_request(self, request):
        """
        This method handles EVERY request that was send by the browser.

        :param request: libmproxy.http.HTTPRequest
        """
        response = None
        try:
            if self.handler_class:
                handler = self.handler_class(self)
                # Send the request to the remote webserver
                req = self._convert_request(request)
                try:
                    res = handler.handle_request(req)
                    if res:
                        response = self._convert_response(res, request)
                except Exception, e:
                    res = handler.send_error(req, e,
                                             trace=str(traceback.format_exc()))
                    if res:
                        response = self._convert_response(res, request)
        except Exception, w:
            om.out.error('The proxy request failed, error: ' + str(w))
        finally:
            request.reply(response)


class ProxyServer(server.ProxyServer):
    pass


class Proxy(Process):
    SSL_CERT = os.path.join(ROOT_PATH, 'core/controllers/daemons/mitm.crt')

    def __init__(self, ip, port, uri_opener, master_class=Master,
                 handler_class=w3afProxyHandler,
                 proxy_cert=SSL_CERT):
        """
        :param ip: IP address to bind
        :param port: Port to bind
        :param uri_opener: The uri_opener that will be used to open
            the requests that arrive from the browser
        :param master_class: A class that will know how to handle
            requests from the browser
        :param proxy_cert: Proxy certificate to use, this is needed
            for proxying SSL connections.
        """
        Process.__init__(self)
        self.daemon = True
        self.name = 'ProxyThread'

        # Internal vars
        self._server = None
        self._running = False
        self._uri_opener = uri_opener

        # User configured parameters
        self._ip = ip
        self._port = port
        self._proxy_cert = proxy_cert
        self._config = config.ProxyConfig(
            clientcerts=self._proxy_cert,
        )
        # Start the proxy server
        try:
            self._server = ProxyServer(self._config, port, ip)
        except server.ProxyServerError, se:
            raise ProxyException(se)
        else:
            # This is here to support port == 0, which will bind to the first
            # available/free port, which we don't know until the server really
            # starts
            self._port = self._server.address.port
        self._master = master_class(self._server, self._uri_opener,
                                    handler=handler_class)

    def get_bind_ip(self):
        """
        :return: The IP address where the proxy will listen.
        """
        return self._ip

    def get_bind_port(self):
        """
        :return: The TCP port where the proxy will listen.
        """
        return self._port

    def is_running(self):
        """
        :return: True if the proxy daemon is running
        """
        return self._running

    def get_port(self):
        if self._server is not None:
            return self._server.address.port

    def wait_for_start(self):
        while self._server is None or self.get_port() is None:
            time.sleep(0.5)

    def run(self):
        """
        Starts the proxy daemon; usually this method isn't called directly. In
        most cases you'll call start()
        """
        om.out.debug('Using proxy master: %s.' % self._master)

        # Starting to handle requests
        message = 'Proxy server listening on %s:%s.' % (self._ip, self._port)
        om.out.debug(message)

        self._running = True
        self._master.run()
        self._running = False

    def stop(self):
        """
        Stop the proxy by setting _go to False and creating a new request.
        """
        om.out.debug('Calling stop of proxy daemon.')
        if self._running:
            self._master.shutdown()