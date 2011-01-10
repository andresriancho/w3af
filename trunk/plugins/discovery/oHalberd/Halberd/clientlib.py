# -*- coding: iso-8859-1 -*-

"""HTTP/HTTPS client module.

@var default_timeout: Default timeout for socket operations.
@type default_timeout: C{float}

@var default_bufsize: Default number of bytes to try to read from the network.
@type default_bufsize: C{int}

@var default_template: Request template, must be filled by L{HTTPClient}
@type default_template: C{str}
"""

# Copyright (C) 2004, 2005, 2006 Juan M. Bello Rivas <jmbr@superadditive.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import time
import socket
import urlparse

from itertools import takewhile

import Halberd.ScanTask


default_timeout = 2

default_bufsize = 1024

# WARNING - Changing the HTTP request method in the following template will
# require updating tests/test_clientlib.py accordingly.
default_template = """\
GET %(request)s HTTP/1.1\r\n\
Host: %(hostname)s%(port)s\r\n\
Pragma: no-cache\r\n\
Cache-control: no-cache\r\n\
User-Agent: Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.7.7) Gecko/20050414 Firefox/1.0.3\r\n\
Accept: image/gif, image/x-xbitmap, image/jpeg, image/pjpeg,\
 application/x-shockwave-flash, */*\r\n\
Accept-Language: en-us,en;q=0.5\r\n\
Accept-Encoding: gzip,deflate\r\n\
Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7\r\n\
Keep-Alive: 300\r\n\
Connection: keep-alive\r\n\r\n\
"""


class HTTPError(Exception):
    """Generic HTTP exception"""

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)

    def __deepcopy__(self, memo):
        return self

class HTTPSError(HTTPError):
    """Generic HTTPS exception"""

class InvalidURL(HTTPError):
    """Invalid or unsupported URL"""

class TimedOut(HTTPError):
    """Operation timed out"""

class ConnectionRefused(HTTPError):
    """Unable to reach webserver"""

class UnknownReply(HTTPError):
    """The remote host didn't return an HTTP reply"""


class HTTPClient:
    """Special-purpose HTTP client.

    @ivar timeout: Timeout for socket operations (expressed in seconds).
    B{WARNING}: changing this value is strongly discouraged.
    @type timeout: C{float}

    @ivar bufsize: Buffer size for network I/O.
    @type bufsize: C{int}

    @ivar template: Template of the HTTP request to be sent to the target.
    @type template: C{str}

    @ivar _recv: Reference to a callable responsible from reading data from the
    network.
    @type _recv: C{callable}
    """
    timeout = default_timeout
    bufsize = default_bufsize
    template = default_template

    def __init__(self):
        """Initializes the object.
        """
        self.schemes = ['http']
        self.default_port = 80
        # _timeout_exceptions MUST be converted to a tuple before using it with
        # except.
        self._timeout_exceptions = [socket.timeout]

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(self.timeout)

        self._recv = self._sock.recv

    def getHeaders(self, address, urlstr):
        """Talk to the target webserver and fetch MIME headers.

        @param address: The target's network address.
        @type address: C{tuple}

        @param urlstr: URL to use.
        @type urlstr: C{str}

        @return: The time when the client started reading the server's response
        and the MIME headers that were sent.
        @rtype: C{tuple}
        """
        self._putRequest(address, urlstr)

        timestamp, headers = self._getReply()
        if not headers:
            return None

        # Remove HTTP response and leave only the MIME headers.
        headers = headers.splitlines()[1:]
        headers = list(takewhile(lambda x: x != '', headers))
        headers.append('\r\n')
        headers = '\r\n'.join(headers)

        return timestamp, headers

    def _putRequest(self, address, urlstr):
        """Sends an HTTP request to the target webserver.

        This method connects to the target server, sends the HTTP request and
        records a timestamp.

        @param address: Target address.
        @type address: C{str}

        @param urlstr: A valid Unified Resource Locator.
        @type urlstr: C{str}

        @raise InvalidURL: In case the URL scheme is not HTTP or HTTPS
        @raise ConnectionRefused: If it can't reach the target webserver.
        @raise TimedOut: If we cannot send the data within the specified time.
        """
        scheme, netloc, url, params, query, fragment = urlparse.urlparse(urlstr)

        if scheme not in self.schemes:
            raise InvalidURL, '%s is not a supported protocol' % scheme

        hostname, port = self._getHostAndPort(netloc)
        # NOTE: address and hostname may not be the same. The caller is
        # responsible for checking that.
            
        req = self._fillTemplate(hostname, port, url, params, query, fragment)

        self._connect((address, port))

        self._sendAll(req)

    def _getHostAndPort(self, netloc):
        """Determine the hostname and port to connect to from an URL

        @param netloc: Relevant part of the parsed URL.
        @type netloc: C{str}

        @return: Hostname (C{str}) and port (C{int})
        @rtype: C{tuple}
        """
        try:
            hostname, portnum = netloc.split(':', 1)
        except ValueError:
            hostname, port = netloc, self.default_port
        else:
            if portnum.isdigit():
                port = int(portnum)
            else:
                raise InvalidURL, '%s is not a valid port number' % portnum

        return hostname, port

    def _fillTemplate(self, hostname, port, url, params='', query='', fragment=''):
        """Fills the request template with relevant information.

        @param hostname: Target host to reach.
        @type hostname: C{str}

        @param port: Remote port.
        @type port: C{int}

        @param url: URL to use as source.
        @type url: C{str}

        @return: A request ready to be sent
        @rtype: C{str}
        """
        urlstr = url or '/'
        if params:
            urlstr += ';' + params
        if query:
            urlstr += '?' + query
        if fragment:
            urlstr += '#' + fragment

        if port == self.default_port:
            p = ''
        else:
            p = ':' + str(port)

        values = {'request': urlstr, 'hostname': hostname, 'port': p}

        return self.template % values

    def _connect(self, addr):
        """Connect to the target address.

        @param addr: The target's address.
        @type addr: C{tuple}

        @raise ConnectionRefused: If it can't reach the target webserver.
        """
        try:
            self._sock.connect(addr)
        except socket.error:
            raise ConnectionRefused, 'Connection refused'

    def _sendAll(self, data):
        """Sends a string to the socket.
        """
        try:
            self._sock.sendall(data)
        except socket.timeout:
            raise TimedOut, 'timed out while writing to the network'

    def _getReply(self):
        """Read a reply from the server.

        @return: Time when the data started arriving plus the received data.
        @rtype: C{tuple}

        @raise UnknownReply: If the remote server doesn't return a valid HTTP
        reply.
        @raise TimedOut: In case reading from the network takes too much time.
        """
        data = ''
        timestamp = None
        stoptime = time.time() + self.timeout
        while time.time() < stoptime:
            try:
                chunk = self._recv(self.bufsize)
            except tuple(self._timeout_exceptions), msg:
                raise TimedOut, msg
    
            if not chunk:
                # The remote end closed the connection.
                break

            if not timestamp:
                timestamp = time.time()

            data += chunk
            idx = data.find('\r\n\r\n')
            if idx != -1:
                data = data[:idx]
                break

        if not data.startswith('HTTP/'):
            raise UnknownReply, 'Invalid protocol'

        return timestamp, data

    def __del__(self):
        if self._sock:
            self._sock.close()


class HTTPSClient(HTTPClient):
    """Special-purpose HTTPS client.
    """

    def __init__(self):
        HTTPClient.__init__(self)

        self.schemes.append('https')

        self.default_port = 443

        self._recv = None
        self._sslsock = None
        self._timeout_exceptions.append(socket.sslerror)

        # Path to an SSL key file and certificate.
        self.keyfile = None
        self.certfile = None

    def _connect(self, addr):
        """Connect to the target web server.

        @param addr: The target's address.
        @type addr: C{tuple}

        @raise HTTPSError: In case there's some mistake during the SSL
        negotiation.
        """
        HTTPClient._connect(self, addr)
        try:
            self._sslsock = socket.ssl(self._sock, self.keyfile, self.certfile)
        except socket.sslerror, msg:
            raise HTTPSError, msg

        self._recv = self._sslsock.read

    def _sendAll(self, data):
        """Sends a string to the socket.
        """
        # xxx - currently we don't make sure everything is sent.
        self._sslsock.write(data)
        

def clientFactory(scantask):
    """HTTP/HTTPS client factory.

    @param scantask: Object describing where the target is and how to reach it.
    @type scantask: C{instanceof(ScanTask)}

    @return: The appropriate client class for the specified URL.
    @rtype: C{class}
    """
    url = scantask.url
    keyfile = scantask.keyfile
    certfile = scantask.certfile

    if url.startswith('http://'):
        return HTTPClient()
    elif url.startswith('https://'):
        httpsclient = HTTPSClient()
        httpsclient.keyfile = keyfile
        httpsclient.certfile = certfile
        return httpsclient
    else:
        raise InvalidURL


# vim: ts=4 sw=4 et
