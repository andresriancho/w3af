from w3af.core.controllers.misc.homeDir import get_home_dir
import os

from OpenSSL import crypto
import socket, ssl


class SSLCertifiacate:
    def __init__(self):
        ssl_dir = os.path.join(get_home_dir(), "ssl")
        self.key_path = os.path.join(ssl_dir, "w3af.key")
        self.cert_path = os.path.join(ssl_dir, "w3af.crt")
        if not os.path.exists(ssl_dir):
            os.makedirs(ssl_dir)

    def generate(self, host=None):
        if host is None:
            host = socket.gethostname()
            key = crypto.PKey()
            key.generate_key(crypto.TYPE_RSA, 2048)
            cert = crypto.X509()
            cert.get_subject().C = "IN"
            cert.get_subject().ST = "TN"
            cert.get_subject().L = "w3af"
            cert.get_subject().O = "W3AF"
            cert.get_subject().OU = "W3AF"
            cert.get_subject().CN = host
            cert.set_serial_number(111111111111111111111111111)
            cert.gmtime_adj_notBefore(0)
            cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
            cert.set_issuer(cert.get_subject())
            cert.set_pubkey(key)
            cert.sign(key, "sha256")

            with open(self.cert_path, "w") as f:
                f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

            with open(self.key_path, "w") as f:
                f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

    def get(self):
        if not os.path.exists(self.cert_path) or not os.path.exists(self.cert_path):
            self.generate()
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain(self.cert_path, self.key_path)
        return context
