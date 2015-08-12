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
import socket
import time
import os

from multiprocessing.dummy import Process
from libmproxy.proxy.server import ProxyServer, ProxyServerError
from libmproxy.proxy.config import ProxyConfig

import w3af.core.controllers.output_manager as om

from w3af import ROOT_PATH
from w3af.core.controllers.daemons.proxy import ProxyHandler
from w3af.core.controllers.exceptions import ProxyException


class Proxy(Process):
    """
    This class defines a simple HTTP proxy, it is mainly used for "complex"
    plugins.

    You should create a proxy instance like this:
        ws = Proxy('127.0.0.1', 8080, url_opener)

    Or like this, if you want to override the proxy handler (most times you
    want to do it!):
        ws = Proxy('127.0.0.1', 8080, url_opener, proxy_handler=ph)

    If the IP:Port is already in use, an exception will be raised while
    creating the ws instance.

    To start the proxy, and given that this is a Process class, you can do this:
        ws.start()

    Or if you don't want a different thread, you can simply call the run method:
        ws.run()

    The proxy handler class is the place where you'll perform all the magic
    stuff, like intercepting requests, modifying them, etc. A good idea if you
    want to code your own proxy handler is to inherit from the proxy handler
    that is already defined in this file (see: ProxyHandler).

    What you basically have to do is to inherit from it:
        class MyProxyHandler(ProxyHandler):

    And redefine the following methods:
        def do_ALL(self)
            Which originally receives a request from the browser, sends it to
            the remote site, receives the response and returns the response to
            the browser. This method is called every time the browser sends a
            new request.

    Things that work:
        - http requests like GET, HEAD, POST, CONNECT
        - https with certs and all (mitmproxy)

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    CA_CERT_DIR = os.path.join(ROOT_PATH, 'core/controllers/daemons/proxy/ca/')

    INCORRECT_SETUP = ('Your OpenSSL setup seems to be broken. The mitmproxy'
                       ' library failed to create the default configuration'
                       ' required to run.\n'
                       '\n'
                       'The original exception is: "%s"\n'
                       '\n'
                       'Please see this [0] github issue for potential'
                       ' workarounds and help.\n'
                       '\n'
                       '[0] https://github.com/mitmproxy/mitmproxy/issues/281')

    def __init__(self, ip, port, uri_opener, handler_klass=ProxyHandler,
                 ca_certs=CA_CERT_DIR, name='ProxyThread'):
        """
        :param ip: IP address to bind
        :param port: Port to bind
        :param uri_opener: The uri_opener that will be used to open
                           the requests that arrive from the browser
        :param handler_klass: A class that will know how to handle
                              requests from the browser
        """
        Process.__init__(self)
        self.daemon = True
        self.name = name
        
        # Internal vars
        self._server = None
        self._running = False
        self._uri_opener = uri_opener
        self._ca_certs = ca_certs

        # Stats
        self.total_handled_requests = 0

        # User configured parameters
        try:
            self._config = ProxyConfig(cadir=self._ca_certs,
                                       ssl_version_client='SSLv23',
                                       ssl_version_server='SSLv23',
                                       host=ip,
                                       port=port)
        except AttributeError as ae:
            if str(ae) == "'module' object has no attribute '_lib'":
                # This is a rare issue with the OpenSSL setup that some users
                # (mostly in mac os) find. Not related with w3af/mitmproxy but
                # with some broken stuff they have
                #
                # https://github.com/mitmproxy/mitmproxy/issues/281
                # https://github.com/andresriancho/w3af/issues/10716
                #
                # AttributeError: 'module' object has no attribute '_lib'
                raise ProxyException(self.INCORRECT_SETUP % ae)

            else:
                # Something unexpected, raise
                raise

        # Setting these options together with ssl_version_client and
        # ssl_version_server set to SSLv23 means that the proxy will allow all
        # types (including insecure) of SSL connections
        self._config.openssl_options_client = None
        self._config.openssl_options_server = None

        # Start the proxy server
        try:
            self._server = ProxyServer(self._config)
        except socket.error, se:
            raise ProxyException('Socket error while starting proxy: "%s"'
                                 % se.strerror)
        except ProxyServerError, pse:
            raise ProxyException('%s' % pse)
        else:
            # This is here to support port == 0, which will bind to the first
            # available/free port, which we don't know until the server really
            # starts
            self._config.port = self.get_port()

        self._master = handler_klass(self._server, self._uri_opener, self)

    def get_bind_ip(self):
        """
        :return: The IP address where the proxy will listen.
        """
        return self._config.host

    def get_bind_port(self):
        """
        :return: The TCP port where the proxy will listen.
        """
        return self._config.port

    def is_running(self):
        """
        :return: True if the proxy daemon is running
        """
        return self._running

    def get_port(self):
        if self._server is not None:
            return self._server.socket.getsockname()[1]
    
    def wait_for_start(self):
        while self._server is None or self.get_port() is None:
            time.sleep(0.5)

    def run(self):
        """
        Starts the proxy daemon; usually this method isn't called directly. In
        most cases you'll call start()
        """
        args = (self._config.host,
                self._config.port,
                self._master.__class__.__name__)
        message = 'Proxy server listening on %s:%s using %s' % args
        om.out.debug(message)

        # Start to handle requests
        self._running = True
        self._master.run()
        self._running = False

    def stop(self):
        """
        Stop the proxy.
        """
        om.out.debug('Calling stop of proxy daemon')
        self._master.shutdown()
