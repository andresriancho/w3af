"""
test_audit_plugin.py

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
import unittest

from nose.plugins.attrib import attr

from w3af.core.data.url.tests.test_xurllib import TimeoutTCPHandler
from w3af.core.data.url.tests.helpers.upper_daemon import UpperDaemon
from w3af.core.data.kb.knowledge_base import kb
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.controllers.w3afCore import w3afCore


@attr('moth')
class TestAuditPlugin(unittest.TestCase):

    def setUp(self):
        kb.cleanup()
        self.w3af = w3afCore()

    def tearDown(self):
        self.w3af.quit()
        kb.cleanup()
    
    def test_audit_return_vulns(self):
        plugin_inst = self.w3af.plugins.get_plugin_inst('audit', 'sqli')
        
        target_url = get_moth_http('/audit/sql_injection/where_string_single_qs.py')
        uri = URL(target_url + '?uname=pablo')
        freq = FuzzableRequest(uri)
        
        vulns = plugin_inst.audit_return_vulns(freq)
        
        self.assertEqual(len(vulns), 1, vulns)
        
        vuln = vulns[0]
        self.assertEquals("syntax error", vuln['error'])
        self.assertEquals("Unknown database", vuln['db'])
        self.assertEquals(target_url, str(vuln.get_url()))        
        
        self.assertEqual(plugin_inst._store_kb_vulns, False)

    def test_http_timeout_with_plugin(self):
        """
        This is very related with the tests at:
            w3af/core/data/url/tests/test_xurllib.py

        Very similar test is TestXUrllib.test_timeout

        :see: https://github.com/andresriancho/w3af/issues/7112
        """
        upper_daemon = UpperDaemon(TimeoutTCPHandler)
        upper_daemon.start()
        upper_daemon.wait_for_start()

        port = upper_daemon.get_port()

        url = URL('http://127.0.0.1:%s/' % port)
        freq = FuzzableRequest(url)

        plugin_inst = self.w3af.plugins.get_plugin_inst('audit', 'sqli')
        plugin_inst._uri_opener.settings.set_configured_timeout(1)
        plugin_inst._uri_opener.clear_timeout()

        # We expect the server to timeout and the response to be a 204
        resp = plugin_inst.get_original_response(freq)
        self.assertEqual(resp.get_url(), url)
        self.assertEqual(resp.get_code(), 204)

        plugin_inst._uri_opener.settings.set_default_values()
