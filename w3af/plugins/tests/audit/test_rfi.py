"""
test_remote_file_include.py

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

from nose.plugins.attrib import attr

import w3af.core.controllers.daemons.webserver as webserver

from w3af.plugins.audit.rfi import RFIWebHandler
from w3af.core.data.constants.ports import REMOTEFILEINCLUDE
from w3af.plugins.tests.helper import PluginTest, PluginConfig


class TestRFI(PluginTest):

    target_rce = 'http://moth/w3af/audit/rfi/vulnerable.php'
    target_read = 'https://moth/w3af/audit/local_file_read/local_file_read.php'

    _run_configs = {
        'remote_rce': {
            'target': target_rce + '?file=section.php',
            'plugins': {
                'audit': (PluginConfig('rfi'),),
            }
        },

        'local_rce': {
            'target': target_rce + '?file=section.php',
            'plugins': {
                'audit': (PluginConfig('rfi',
                                       (
                                       'use_w3af_site', False, PluginConfig.BOOL),),),
            }
        },

        'local_read': {
            'target': target_read + '?file=section.txt',
            'plugins': {
                'audit': (PluginConfig('rfi',
                                       (
                                       'use_w3af_site', False, PluginConfig.BOOL),),),
            }
        },

        'remote_read': {
            'target': target_read + '?file=section.txt',
            'plugins': {
                'audit': (PluginConfig('rfi',
                                       (
                                       'use_w3af_site', False, PluginConfig.BOOL),),),
            }
        }

    }

    @attr('ci_fails')
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
    @attr('ci_fails')
    def test_found_rfi_with_local_server_rce(self):
        cfg = self._run_configs['local_rce']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('rfi', 'rfi')
        self.assertEquals(len(vulns), 1)

        vuln = vulns[0]
        self.assertEquals("Remote code execution", vuln.get_name())
        self.assertEquals(self.target_rce, vuln.get_url().url_string)

    @attr('ci_fails')
    def test_found_rfi_with_local_server_read(self):
        cfg = self._run_configs['local_read']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('rfi', 'rfi')
        self.assertEquals(len(vulns), 1)

        vuln = vulns[0]
        self.assertEquals("Remote file inclusion", vuln.get_name())
        self.assertEquals(self.target_read, vuln.get_url().url_string)

    @attr('ci_fails')
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
        webserver.start_webserver(
            '127.0.0.1', REMOTEFILEINCLUDE, '.', RFIWebHandler)

        response_foobar = urllib2.urlopen(
            'http://localhost:44449/foobar').read()
        response_spameggs = urllib2.urlopen(
            'http://localhost:44449/spameggs').read()

        self.assertEqual(response_foobar, response_spameggs)
        self.assertEqual(response_foobar, RFIWebHandler.RESPONSE_BODY)