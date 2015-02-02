"""
Based heavily on code from:
https://github.com/t-8ch/requests/blob/d7908a9fdef7bca16e384ca42478d69d1894c8b6/requests/packages/urllib3/contrib/pyopenssl.py
"""
import socket
import ssl
import OpenSSL
import pyasn1.codec.der.decoder
import subj_alt_name

PROTOCOL_SSLv23 = ssl.PROTOCOL_SSLv23
PROTOCOL_SSLv3 = ssl.PROTOCOL_SSLv3
PROTOCOL_TLSv1 = ssl.PROTOCOL_TLSv1

CERT_NONE = ssl.CERT_NONE
CERT_OPTIONAL = ssl.CERT_OPTIONAL
CERT_REQUIRED = ssl.CERT_REQUIRED

_openssl_versions = {
    PROTOCOL_SSLv23: OpenSSL.SSL.SSLv23_METHOD,
    PROTOCOL_SSLv3: OpenSSL.SSL.SSLv3_METHOD,
    PROTOCOL_TLSv1: OpenSSL.SSL.TLSv1_METHOD,
}

_openssl_cert_reqs = {
    CERT_NONE: OpenSSL.SSL.VERIFY_NONE,
    CERT_OPTIONAL: OpenSSL.SSL.VERIFY_PEER,
    CERT_REQUIRED: OpenSSL.SSL.VERIFY_PEER | \
            OpenSSL.SSL.VERIFY_FAIL_IF_NO_PEER_CERT
}


class SSLSocket(object):
    def __init__(self, connection, sock):
        self.connection = connection
        self.sock = sock

    def makefile(self, mode, bufsize=-1):
        return socket._fileobject(self.connection, mode, bufsize)

    def getpeercert(self, binary_form=False):
        x509 = self.connection.get_peer_certificate()
        if not x509:
            raise ssl.SSLError('')

        if binary_form:
            return OpenSSL.crypto.dump_certificate(
                OpenSSL.crypto.FILETYPE_ASN1,
                x509)

        dns_name = []
        general_names = subj_alt_name.SubjectAltName()

        for i in range(x509.get_extension_count()):
            ext = x509.get_extension(i)
            ext_name = ext.get_short_name()
            if ext_name != 'subjectAltName':
                continue

            ext_dat = ext.get_data()
            der_decoder = pyasn1.codec.der.decoder
            decoded_dat = der_decoder.decode(ext_dat,
                                             asn1Spec=general_names)

            for name in decoded_dat:
                if not isinstance(name, subj_alt_name.SubjectAltName):
                    continue
                for entry in range(len(name)):
                    component = name.getComponentByPosition(entry)
                    if component.getName() != 'dNSName':
                        continue
                    dns_name.append(('DNS', str(component.getComponent())))

        return {
            'subject': (
                (('commonName', x509.get_subject().CN),),
            ),
            'subjectAltName': dns_name
        }

    # Pass any un-handle function calls on to connection
    def __getattr__(self, name):
        try:
            return getattr(self.connection, name)
        except AttributeError:
            return getattr(self.sock, name)


class OpenSSLReformattedError(Exception):
    def __init__(self, e):
        self.e = e

    def __str__(self):
        try:
            return '*:%s:%s (glob)' % (self.e.args[0][0][1], self.e.args[0][0][2])
        except Exception:
            return '%s'%self.e


def wrap_socket(sock, keyfile=None, certfile=None, server_side=False,
                cert_reqs=CERT_NONE, ssl_version=PROTOCOL_TLSv1,
                ca_certs=None, do_handshake_on_connect=True,
                suppress_ragged_eofs=True, server_hostname=None,
                timeout=None):
    cert_reqs = _openssl_cert_reqs[cert_reqs]
    ssl_version = _openssl_versions[ssl_version]

    ctx = OpenSSL.SSL.Context(ssl_version)
    if certfile:
        ctx.use_certificate_file(certfile)
    if keyfile:
        ctx.use_privatekey_file(keyfile)
    if cert_reqs != OpenSSL.SSL.VERIFY_NONE:
        ctx.set_verify(cert_reqs, lambda a, b, err_no, c, d: err_no == 0)
    if timeout is not None:
        ctx.set_timeout(timeout)
    if ca_certs:
        try:
            ctx.load_verify_locations(ca_certs, None)
        except OpenSSL.SSL.Error, e:
            raise ssl.SSLError('Bad ca_certs: %r' % ca_certs,
                               OpenSSLReformattedError(e))

    cnx = OpenSSL.SSL.Connection(ctx, sock)
    if server_hostname is not None:
        cnx.set_tlsext_host_name(server_hostname)
    cnx.set_connect_state()

    try:
        cnx.do_handshake()
    except OpenSSL.SSL.Error, e:
        raise ssl.SSLError('Bad handshake',
                           OpenSSLReformattedError(e))

    return SSLSocket(cnx, sock)

