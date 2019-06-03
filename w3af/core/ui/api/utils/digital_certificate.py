"""
digital_certificate.py

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
import os
import socket

from OpenSSL import crypto
from w3af.core.controllers.misc.home_dir import get_home_dir


class SSLCertificate(object):
    def __init__(self):
        ssl_dir = os.path.join(get_home_dir(), 'ssl')
        self.key_path = os.path.join(ssl_dir, 'w3af.key')
        self.cert_path = os.path.join(ssl_dir, 'w3af.crt')
        if not os.path.exists(ssl_dir):
            os.makedirs(ssl_dir)

    def generate(self, host=None):
        """
        :param host: The hostname used to generate the certificate
        :return: None, we write the cert and key to files
        """
        if host is None:
            host = socket.gethostname()

        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 2048)
        cert = crypto.X509()
        cert.get_subject().C = 'US'
        cert.get_subject().ST = 'CA'
        cert.get_subject().L = 'w3af.org'
        cert.get_subject().O = 'w3af.org'
        cert.get_subject().OU = 'w3af.org'
        cert.get_subject().CN = host
        cert.set_serial_number(111111111111111111111111111)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(key)
        cert.sign(key, 'sha256')

        with open(self.cert_path, 'w') as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

        with open(self.key_path, 'w') as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

    def get_cert_key(self, host=None):
        """
        :param host: The hostname used to generate the certificate
        :return: A tuple containing:
                    - Certificate path
                    - Key path
        """
        if not os.path.exists(self.cert_path) or not os.path.exists(self.cert_path):
            self.generate(host=host)

        # context = SSL.Context(SSL.TLSv1_2_METHOD)
        # context.use_privatekey_file(self.key_path)
        # context.use_certificate_file(self.cert_path)

        #
        # Flask/Werkzeug have an issue where in one version they supported
        # SSL.Context (from the OpenSSL library) and then they deprecated that
        # when ssl.Context appeared in 2.7.9. The problem with this change is
        # that we don't want to force w3af users to migrate to python 2.7.9,
        # and we don't want to downgrade our flask/werkzeug version might break
        # things or add bugs.
        #
        # https://github.com/mitsuhiko/flask/issues/1352
        # https://stackoverflow.com/questions/28579142/attributeerror-context-object-has-no-attribute-wrap-socket
        #
        # For some strange reason flask's run method can receive a ssl_context
        # which contains a tuple with cert file and key, and that works in
        # my 2.7.6 python. So returning that!
        #
        return self.cert_path, self.key_path
