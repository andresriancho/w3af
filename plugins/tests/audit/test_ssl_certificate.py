'''
test_ssl_certificate.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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
'''

import os
import socket, ssl
import threading
import random

from ..helper import PluginTest, PluginConfig

PORT = random.randint(4443,4599)

       
class TestSSLCertificate(PluginTest):
    
    target_url = 'https://localhost:%s/' % PORT
    
    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                 'audit': (PluginConfig('sslCertificate'),),
                 }
            }
        }
    
    def test_ssl_certificate(self):
        # Start the HTTPS server
        certfile = os.path.join('plugins','tests','audit', 'certs', 'invalid_cert.pem')
        s = ssl_server('localhost', PORT, certfile)
        s.start()
        
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        s.stop()
                
        vulns = self.kb.getData('sslCertificate', 'invalid_ssl_cert')

        self.assertEquals(1, len(vulns))
        
        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals('Invalid SSL certificate',vuln.getName())
        self.assertEquals(self.target_url, str(vuln.getURL()))



HTTP_RESPONSE = '''HTTP/1.1 200 Ok\r\nConnection: close\r\nContent-Length: 3\r\n\r\nabc'''
        
class ssl_server(threading.Thread):

    def __init__(self, listen, port, certfile, proto=ssl.PROTOCOL_SSLv3):
        threading.Thread.__init__(self)
        self.listen = listen
        self.port = port
        self.cert = certfile
        self.proto = proto
        self.sock = socket.socket()
        self.sock.bind((listen, port))
        self.sock.listen(5)

    def accept(self):
        self.sock = ssl.wrap_socket(self.sock,
                                    server_side=True,
                                    certfile=self.cert,
                                    cert_reqs=ssl.CERT_NONE,
                                    ssl_version= self.proto,
                                    do_handshake_on_connect=False,
                                    suppress_ragged_eofs=True)

        newsocket, fromaddr = self.sock.accept()

        try:
            newsocket.do_handshake()
        except:
            # The ssl certificate might request a connection with
            # SSL protocol v2 and that will "break" the handshake
            pass

        print 'Connection from ', fromaddr
        try:
            newsocket.send(HTTP_RESPONSE)
        except:
            print 'Connection closed by remote end.'
        finally:
            newsocket.close()

    def run(self):
        self.should_stop = False
        while not self.should_stop:
            self.accept()

    def stop(self):
        self.should_stop = True
        try:
            self.sock.close()
    
            # Connection to force stop,
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.listen, self.port))
            s.close()
        except:
            pass