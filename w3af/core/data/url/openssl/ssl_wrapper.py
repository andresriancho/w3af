"""
Based heavily on code from:
    https://code.google.com/p/ssl-sni/source/browse/ssl_sni/openssl.py

Which uses the GNU Affero General Public License >= 3 , but that code is
actually based heavily on code from:
    https://github.com/t-8ch/requests/blob/d7908a9fdef7bca16e384ca42478d69d1894c8b6/requests/packages/urllib3/contrib/pyopenssl.py

Which is actually part of the "requests" project that's released under Apache
License, Version 2.0.

IANAL but I believe that the guys from ssl-sni made a mistake at changing the
license (basically they can't). So I'm choosing to use the original Apache
License, Version 2.0 for this file.
"""
import ssl
import time
import socket
import select
import OpenSSL

from ndg.httpsclient.subj_alt_name import SubjectAltName
from pyasn1.codec.der.decoder import decode as der_decoder

CERT_NONE = ssl.CERT_NONE
CERT_OPTIONAL = ssl.CERT_OPTIONAL
CERT_REQUIRED = ssl.CERT_REQUIRED

_openssl_cert_reqs = {
    CERT_NONE: OpenSSL.SSL.VERIFY_NONE,
    CERT_OPTIONAL: OpenSSL.SSL.VERIFY_PEER,
    CERT_REQUIRED: OpenSSL.SSL.VERIFY_PEER | \
            OpenSSL.SSL.VERIFY_FAIL_IF_NO_PEER_CERT
}


class SSLSocket(object):
    """
    This class was required to avoid the issue of "Bad file descriptor" which
    is generated when the remote server returns a connection: close header,
    which will trigger a self.close() in httplib's:

    def getresponse(self, buffering=False):
        ...
        if response.will_close:
            # this effectively passes the connection to the response
            self.close()

    Calling that self.close() will close the openssl connection, which we then
    read() to retrieve the http response body.

    Connection is not yet a new-style class, so I'm making a proxy instead of
    subclassing. Inspiration for this class comes from certmaster's source code

    Another reason for this wrapper is to implement timeouts for recv() and sendall()
    which require some ugly calls to select.select() because of pyopenssl limitations [2]

    [0] https://github.com/andresriancho/w3af/issues/8125
    [1] https://github.com/mpdehaan/certmaster/blob/master/certmaster/SSLConnection.py
    [2] https://github.com/andresriancho/w3af/issues/7989
    """
    def __init__(self, ssl_connection, sock):
        """
        :param ssl_connection: The established openssl connection
        :param sock: The underlying tcp/ip connection
        """
        self.ssl_conn = ssl_connection
        self.sock = sock
        self.close_refcount = 1
        self.closed = False

    def __getattr__(self, name):
        """
        Pass any un-handled function calls on to connection
        """
        try:
            return getattr(self.ssl_conn, name)
        except AttributeError:
            return getattr(self.sock, name)

    def makefile(self, mode, bufsize):
        """
        We need to use socket._fileobject Because SSL.Connection
        doesn't have a 'dup'. Not exactly sure WHY this is, but
        this is backed up by comments in socket.py and SSL/connection.c

        Since httplib.HTTPSResponse/HTTPConnection depend on the
        socket being duplicated when they close it, we refcount the
        socket object and don't actually close until its count is 0.
        """
        self.close_refcount += 1
        return socket._fileobject(self, mode, bufsize, close=True)

    def close(self):
        if self.closed:
            return

        self.close_refcount -= 1
        if self.close_refcount == 0:

            try:
                self.shutdown()
            except OpenSSL.SSL.Error, ssl_error:
                message = str(ssl_error)
                if not message:
                    # We get here when the remote end already closed the
                    # connection. The shutdown() call to the OpenSSLConnection
                    # simply fails with an exception without a message
                    #
                    # This was needed to support SSLServer (ssl_daemon.py)
                    # but will also be useful for other real-life cases
                    pass
                else:
                    # We don't know what's here, raise!
                    raise

            # Close doesn't seem to mind if the remote end already closed the
            # connection
            self.ssl_conn.close()
            self.closed = True

    def recv(self, *args, **kwargs):
        try:
            data = self.ssl_conn.recv(*args, **kwargs)
        except OpenSSL.SSL.ZeroReturnError:
            # empty string signalling that the other side has closed the
            # connection or that some kind of error happen and no more reads
            # should be done on this socket
            return ''
        except OpenSSL.SSL.WantReadError:
            rd, wd, ed = select.select([self.sock], [], [], self.sock.gettimeout())
            if not rd:
                # empty string signalling that the other side has closed the
                # connection or that some kind of error happen and no more reads
                # should be done on this socket
                return ''
            else:
                return self.recv(*args, **kwargs)
        else:
            return data

    def settimeout(self, timeout):
        return self.sock.settimeout(timeout)

    def _send_until_done(self, data):
        while True:
            try:
                return self.ssl_conn.send(data)
            except OpenSSL.SSL.WantWriteError:
                _, wlist, _ = select.select([], [self.sock], [], self.sock.gettimeout())
                if not wlist:
                    raise socket.timeout()
                continue

    def sendall(self, data):
        while len(data):
            sent = self._send_until_done(data)
            data = data[sent:]

    def getpeercert(self, binary_form=False):
        """
        :return: The remote peer certificate in a tuple
        """
        x509 = self.ssl_conn.get_peer_certificate()
        if not x509:
            raise ssl.SSLError('No peer certificate')

        if binary_form:
            return OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_ASN1,
                                                   x509)

        dns_name = []
        general_names = SubjectAltName()

        for i in xrange(x509.get_extension_count()):
            ext = x509.get_extension(i)
            ext_name = ext.get_short_name()

            if ext_name != 'subjectAltName':
                continue

            ext_dat = ext.get_data()
            decoded_dat = der_decoder(ext_dat, asn1Spec=general_names)

            for name in decoded_dat:
                if not isinstance(name, SubjectAltName):
                    continue
                for entry in xrange(len(name)):
                    component = name.getComponentByPosition(entry)
                    if component.getName() != 'dNSName':
                        continue
                    dns_name.append(('DNS', str(component.getComponent())))

        return {
            'subject': (
                (('commonName', x509.get_subject().CN),),
            ),
            'subjectAltName': dns_name,
            'notAfter': x509.get_notAfter()
        }


class OpenSSLReformattedError(Exception):
    def __init__(self, e):
        self.e = e

    def __str__(self):
        try:
            return '*:%s:%s (glob)' % (self.e.args[0][0][1],
                                       self.e.args[0][0][2])
        except Exception:
            return '%s' % self.e


def wrap_socket(sock, keyfile=None, certfile=None, server_side=False,
                cert_reqs=CERT_NONE, ssl_version=OpenSSL.SSL.TLSv1_1_METHOD,
                ca_certs=None, do_handshake_on_connect=True,
                suppress_ragged_eofs=True, server_hostname=None,
                timeout=None):
    """
    Make a classic socket SSL aware

    :param sock: The classic TCP/IP socket
    :return: An SSLSocket instance
    """
    cert_reqs = _openssl_cert_reqs[cert_reqs]

    ctx = OpenSSL.SSL.Context(ssl_version)

    if certfile:
        ctx.use_certificate_file(certfile)

    if keyfile:
        ctx.use_privatekey_file(keyfile)

    if cert_reqs != OpenSSL.SSL.VERIFY_NONE:
        ctx.set_verify(cert_reqs, lambda a, b, err_no, c, d: err_no == 0)

    if ca_certs:
        try:
            ctx.load_verify_locations(ca_certs, None)
        except OpenSSL.SSL.Error, e:
            raise ssl.SSLError('Bad ca_certs: %r' % ca_certs, e)

    cnx = OpenSSL.SSL.Connection(ctx, sock)

    # SNI support
    if server_hostname is not None:
        cnx.set_tlsext_host_name(server_hostname)

    cnx.set_connect_state()

    # SSL connection timeout doesn't work #7989 , so I'm not able to call:
    #   ctx.set_timeout(timeout)
    #
    # The workaround I found was to use select.select and non-blocking sockets,
    # and was implemented in SSLSocket (see above).
    #
    # Note that by setting the "sock" instance timeout, I'm also enforcing the
    # SSL connection timeout because of the fourth parameter sent to
    # select.select() in recv() and sendall().
    #
    # More information at:
    #    https://github.com/andresriancho/w3af/issues/7989
    sock.setblocking(0)
    sock.settimeout(timeout)
    time_begin = time.time()

    while True:
        try:
            cnx.do_handshake()
            break
        except OpenSSL.SSL.WantReadError:
            in_fds, out_fds, err_fds = select.select([sock, ], [], [], timeout)
            if len(in_fds) == 0:
                raise ssl.SSLError('do_handshake timed out')
            else:
                conn_time = int(time.time() - time_begin)
                if conn_time > timeout:
                    raise ssl.SSLError('do_handshake timed out')
                else:
                    pass
        except OpenSSL.SSL.SysCallError as e:
            raise ssl.SSLError(e.args)

    sock.setblocking(1)
    ssl_socket = SSLSocket(cnx, sock)
    ssl_socket.settimeout(timeout)
    
    return ssl_socket

