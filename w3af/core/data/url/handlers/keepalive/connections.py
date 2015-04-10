import threading
import binascii
import httplib
import urllib
import socket
import ssl
import os

from .http_response import HTTPResponse
from .utils import debug, DEBUG

from w3af.core.controllers.exceptions import HTTPRequestException
from w3af.core.data.url.openssl.ssl_wrapper import wrap_socket


class UniqueID(object):
    def __init__(self):
        if DEBUG:
            # Only do the extra id stuff when debugging
            self.id = binascii.hexlify(os.urandom(8))
        else:
            self.id = None

        self.req_count = 0
        self.timeout = None

    def inc_req_count(self):
        self.req_count += 1

    def __repr__(self):
        # Only makes sense when DEBUG is True
        return '<KeepAliveHTTPConnection %s - Request #%s>' % (self.id,
                                                               self.req_count)

    def __str__(self):
        # Only makes sense when DEBUG is True
        timeout = None if self.timeout is socket._GLOBAL_DEFAULT_TIMEOUT else self.timeout
        args = (self.__class__.__name__, self.id, self.req_count, timeout)
        return '%s(id:%s, req_count:%s, timeout:%s)' % args


class _HTTPConnection(httplib.HTTPConnection, UniqueID):

    def __init__(self, host, port=None, strict=None,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        UniqueID.__init__(self)
        httplib.HTTPConnection.__init__(self, host, port, strict,
                                        timeout=timeout)
        self.is_fresh = True


class ProxyHTTPConnection(_HTTPConnection):
    """
    This class is used to provide HTTPS CONNECT support.
    """
    _ports = {'http': 80, 'https': 443}

    def __init__(self, host, port=None, strict=None,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        _HTTPConnection.__init__(self, host, port, strict, timeout=timeout)

    def proxy_setup(self, url):
        # request is called before connect, so can interpret url and get
        # real host/port to be used to make CONNECT request to proxy
        proto, rest = urllib.splittype(url)
        if proto is None:
            raise ValueError("unknown URL type: %s" % url)

        # get host
        host, rest = urllib.splithost(rest)
        self._real_host = host

        # try to get port
        host, port = urllib.splitport(host)

        # if port is not defined try to get from proto
        if port is None:
            try:
                self._real_port = self._ports[proto]
            except KeyError:
                raise ValueError("unknown protocol for: %s" % url)
        else:
            self._real_port = int(port)

    def connect(self):
        httplib.HTTPConnection.connect(self)

        #send proxy CONNECT request
        new_line = '\r\n'
        self.send("CONNECT %s:%d HTTP/1.1%s" % (self._real_host,
                                                self._real_port,
                                                new_line))

        connect_headers = {'Proxy-Connection': 'keep-alive',
                           'Connection': 'keep-alive',
                           'Host': self._real_host}

        for header_name, header_value in connect_headers.items():
            self.send('%s: %s%s' % (header_name, header_value, new_line))

        self.send(new_line)

        #expect a HTTP/1.0 200 Connection established
        response = self.response_class(self.sock, strict=self.strict,
                                       method=self._method)
        version, code, message = response._read_status()

        #probably here we can handle auth requests...
        if code != 200:
            #proxy returned and error, abort connection, and raise exception
            self.close()
            raise socket.error("Proxy connection failed: %d %s" %
                              (code, message.strip()))

        # eat up header block from proxy....
        while True:
            #should not use directly fp probably
            line = response.fp.readline()
            if line == '\r\n':
                break

# https://bugs.kali.org/view.php?id=2160
proto_names = ('PROTOCOL_SSLv3',
               'PROTOCOL_TLSv1',
               'PROTOCOL_SSLv23',
               'PROTOCOL_SSLv2')
_protocols = filter(None, (getattr(ssl, pn, None) for pn in proto_names))

# Avoid race conditions
_protocols_lock = threading.RLock()


class SSLNegotiatorConnection(httplib.HTTPSConnection, UniqueID):
    """
    Connection class that enables usage of newer SSL protocols.

    References:
        http://bugs.python.org/msg128686
        https://github.com/andresriancho/w3af/issues/5802
        https://gist.github.com/flandr/74be22d1c3d7c1dfefdd
    """
    def __init__(self, *args, **kwargs):
        UniqueID.__init__(self)
        httplib.HTTPSConnection.__init__(self, *args, **kwargs)

    def connect(self):
        """
        Test the different SSL protocols
        """
        for protocol in _protocols:
            sock = self.connect_socket()
            sock = self.make_ssl_aware(sock, protocol)
            if sock is not None:
                break
        else:
            msg = 'Unable to create a SSL connection using protocols: %s'
            protocols = ', '.join([str(p) for p in _protocols])
            raise HTTPRequestException(msg % protocols)

    def connect_socket(self):
        """
        :return: fresh TCP/IP connection
        """
        sock = socket.create_connection((self.host, self.port))

        if getattr(self, "_tunnel_host", None):
            self.sock = sock
            self._tunnel()

        return sock

    def make_ssl_aware(self, sock, protocol):
        """
        Make the socket SSL aware
        """
        try:
            ssl_sock = wrap_socket(sock,
                                   keyfile=self.key_file,
                                   certfile=self.cert_file,
                                   ssl_version=protocol,
                                   server_hostname=self.host,
                                   timeout=self.timeout)
        except ssl.SSLError, ssl_exc:
            msg = "SSL connection error occurred with protocol %s: '%s'"
            debug(msg % (protocol, ssl_exc.__class__.__name__))

            # Always close the tcp/ip connection on error
            sock.close()

        except Exception, e:
            msg = "Unexpected exception occurred with protocol %s: '%s'"
            debug(msg % (protocol, e))

            # Always close the tcp/ip connection on error
            sock.close()

        else:
            debug('Successful connection using protocol %s' % protocol)
            self.sock = ssl_sock
            with _protocols_lock:
                _protocols.remove(protocol)
                _protocols.insert(0, protocol)
            return ssl_sock

        return None


class ProxyHTTPSConnection(ProxyHTTPConnection, SSLNegotiatorConnection):
    """
    This class is used to provide HTTPS CONNECT support.
    """
    default_port = 443

    # Customized response class
    response_class = HTTPResponse

    def __init__(self, host, port=None, key_file=None, cert_file=None,
                 strict=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        UniqueID.__init__(self)
        ProxyHTTPConnection.__init__(self, host, port, strict=strict,
                                     timeout=timeout)
        self.key_file = key_file
        self.cert_file = cert_file

    def connect(self):
        """
        Connect using different SSL protocols
        """
        for protocol in _protocols:
            ProxyHTTPConnection.connect(self)
            self.sock = self.make_ssl_aware(self.sock, protocol)
            if self.sock is not None:
                break
        else:
            msg = 'Unable to create a proxied SSL connection'
            raise HTTPRequestException(msg)


class HTTPConnection(_HTTPConnection):
    # use the modified response class
    response_class = HTTPResponse

    def __init__(self, host, port=None, strict=None,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        _HTTPConnection.__init__(self, host,
                                 port=port,
                                 strict=strict,
                                 timeout=timeout)


class HTTPSConnection(SSLNegotiatorConnection):
    response_class = HTTPResponse

    def __init__(self, host, port=None, key_file=None, cert_file=None,
                 strict=None, timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        SSLNegotiatorConnection.__init__(self, host, port, key_file, cert_file,
                                         strict, timeout=timeout)
        self.is_fresh = True

