"""
test_rfi.py

Copyright 2012 Andres Riancho

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
import urllib2
import threading

from nose.plugins.attrib import attr

from w3af.core.controllers.ci.php_moth import get_php_moth_http
from w3af.core.controllers.daemons.webserver import HTTPServer
from w3af.core.controllers.misc.get_unused_port import get_unused_port
from w3af.plugins.audit.rfi import RFIWebHandler
from w3af.plugins.tests.helper import PluginTest, PluginConfig


class TestRFI(PluginTest):

    target_rce = get_php_moth_http('/audit/rfi/rfi-rce.php')
    target_read = get_php_moth_http('/audit/rfi/rfi-read.php')
    unused_port = get_unused_port()

    _run_configs = {
        'remote_rce': {
            'target': target_rce + '?file=abc.txt',
            'plugins': {
                'audit': (PluginConfig('rfi'),),
            }
        },

        'local_rce': {
            'target': target_rce + '?file=abc.txt',
            'plugins': {
                'audit': (PluginConfig('rfi',
                                       ('use_w3af_site', False, PluginConfig.BOOL),
                                       ('listen_port', unused_port, PluginConfig.INT)),),
            }
        },

        'local_read': {
            'target': target_read + '?file=abc.txt',
            'plugins': {
                'audit': (PluginConfig('rfi',
                                       ('use_w3af_site', False, PluginConfig.BOOL),
                                       ('listen_port', unused_port, PluginConfig.INT)),),
            }
        },

        'remote_read': {
            'target': target_read + '?file=abc.txt',
            'plugins': {
                'audit': (PluginConfig('rfi',
                                       ('use_w3af_site', False, PluginConfig.BOOL),
                                       ('listen_port', unused_port, PluginConfig.INT)),),
            }
        }

    }

    def test_found_rfi_with_w3af_site(self):
        cfg = self._run_configs['remote_rce']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('rfi', 'rfi')
        self.assertEquals(len(vulns), 1)

        vuln = vulns[0]
        self.assertEquals("Remote code execution", vuln.get_name())
        self.assertEquals(self.target_rce, vuln.get_url().url_string)

    @attr('smoke')
    def test_found_rfi_with_local_server_rce(self):
        cfg = self._run_configs['local_rce']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('rfi', 'rfi')
        self.assertEquals(len(vulns), 1)

        vuln = vulns[0]
        self.assertEquals("Remote code execution", vuln.get_name())
        self.assertEquals(self.target_rce, vuln.get_url().url_string)

    def test_found_rfi_with_local_server_read(self):
        cfg = self._run_configs['local_read']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('rfi', 'rfi')
        self.assertEquals(len(vulns), 1)

        vuln = vulns[0]
        self.assertEquals("Remote file inclusion", vuln.get_name())
        self.assertEquals(self.target_read, vuln.get_url().url_string)

    def test_found_rfi_with_remote_server_read(self):
        cfg = self._run_configs['remote_read']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('rfi', 'rfi')
        self.assertEquals(len(vulns), 1)

        vuln = vulns[0]
        self.assertEquals("Remote file inclusion", vuln.get_name())
        self.assertEquals(self.target_read, vuln.get_url().url_string)

    def test_custom_web_server(self):
        RFIWebHandler.RESPONSE_BODY = '<? echo "hello world"; ?>'
        ws = HTTPServer(('127.0.0.1', 0), '.', RFIWebHandler)
        ws.wait_for_start()
        port = ws.get_port()

        server_thread = threading.Thread(target=ws.serve_forever)
        server_thread.name = 'WebServer'
        server_thread.daemon = True
        server_thread.start()

        foobar_url = 'http://localhost:%s/foobar' % port
        spameggs_url = 'http://localhost:%s/spameggs' % port

        response_foobar = urllib2.urlopen(foobar_url).read()
        response_spameggs = urllib2.urlopen(spameggs_url).read()

        self.assertEqual(response_foobar, response_spameggs)
        self.assertEqual(response_foobar, RFIWebHandler.RESPONSE_BODY)