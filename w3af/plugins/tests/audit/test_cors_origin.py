"""
test_cors_origin.py

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
from nose.plugins.attrib import attr

from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.plugins.audit.cors_origin import cors_origin
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.kb.info_set import InfoSet
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers


class TestCORSOriginScan(PluginTest):

    # Test scripts host/port and web context root
    target_url = 'http://moth/w3af/audit/cors/'

    # Originator for tests cases
    originator = 'http://moth/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (
                    PluginConfig(
                        'cors_origin',
                        ('origin_header_value',
                         originator, PluginConfig.STR),
                        ('expected_http_response_code',
                         200, PluginConfig.INT),
                    ),
                ),
                'crawl': (
                    PluginConfig(
                        'web_spider',
                        ('only_forward', True, PluginConfig.BOOL)),
                ),
            }
        }
    }

    @attr('ci_fails')
    def test_scan(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        vulns = self.kb.get('cors_origin', 'cors_origin')
        self.assertEquals(2, len(vulns), vulns)

        EXPECTED_NAMES = ['Insecure Access-Control-Allow-Origin',
                          'Insecure Access-Control-Allow-Origin']

        self.assertEqual([v.get_name() for v in vulns],
                         EXPECTED_NAMES)

        self.assertTrue(all([v.get_url().url_string.startswith(self.target_url)
                             for v in vulns]))


class TestCORSOrigin(PluginTest):
    def setUp(self):
        super(TestCORSOrigin, self).setUp()

        self.co = cors_origin()

        self.url = URL('http://moth/')
        self.origin = 'http://moth/'
        self.response = HTTPResponse(200, '', Headers(), self.url,
                                     self.url, _id=3)
        self.request = FuzzableRequest(self.url)

    def test_allow_methods_no(self):
        allow_methods = 'GET, POST, Options'
        allow_origin = 'http://w3af.org/'
        allow_credentials = 'false'

        self.co._allow_methods(self.request, self.url, self.origin,
                               self.response, allow_origin, allow_credentials,
                               allow_methods)
        vulns = self.kb.get('cors_origin', 'cors_origin')

        self.assertEqual(vulns, [])

    def test_allow_methods_strange(self):

        allow_methods = 'GET, POST, OPTIONS, FOO'
        allow_origin = 'http://w3af.org/'
        allow_credentials = 'false'

        self.co._allow_methods(self.request, self.url, self.origin,
                               self.response, allow_origin, allow_credentials,
                               allow_methods)
        vulns = self.kb.get('cors_origin', 'cors_origin')

        self.assertEqual(len(vulns), 1)
        vuln = vulns[0]

        self.assertEqual(vuln.get_name(), 'Uncommon CORS methods enabled')
        self.assertNotEqual(vuln.get_desc(), None)

    def test_allow_methods_sensitive(self):

        allow_methods = 'GET, POST, OPTIONS, PUT'
        allow_origin = 'http://w3af.org/'
        allow_credentials = 'false'

        self.co._allow_methods(self.request, self.url, self.origin,
                               self.response, allow_origin, allow_credentials,
                               allow_methods)
        vulns = self.kb.get('cors_origin', 'cors_origin')

        self.assertEqual(len(vulns), 1)
        vuln = vulns[0]

        self.assertEqual(vuln.get_name(), 'Sensitive CORS methods enabled')
        self.assertNotEqual(vuln.get_desc(), None)

    def test_allow_methods_sensitive_strange(self):

        allow_methods = 'GET, POST, OPTIONS, PUT, FOO'
        allow_origin = 'http://w3af.org/'
        allow_credentials = 'false'

        self.co._allow_methods(self.request, self.url, self.origin,
                               self.response, allow_origin, allow_credentials,
                               allow_methods)
        vulns = self.kb.get('cors_origin', 'cors_origin')

        self.assertEqual(len(vulns), 2)
        vuln_names = set([v.get_name() for v in vulns])
        expected_vuln_names = {'Sensitive CORS methods enabled',
                               'Uncommon CORS methods enabled'}

        self.assertEqual(vuln_names, expected_vuln_names)
        self.assertIsNotNone(vulns[0].get_desc())
        self.assertIsNotNone(vulns[1].get_desc())

    def test_allow_methods_sensitive_call_max(self):

        allow_methods = 'GET, POST, OPTIONS, PUT'
        allow_origin = 'http://w3af.org/'
        allow_credentials = 'false'

        for i in xrange(InfoSet.MAX_INFO_INSTANCES + 2):

            self.co._allow_methods(self.request, self.url, self.origin,
                                   self.response, allow_origin,
                                   allow_credentials, allow_methods)
            vulns = self.kb.get('cors_origin', 'cors_origin')

            self.assertEqual(len(vulns), 1)
            v = vulns[0]

            msg = 'Failure on run #%s' % i
            self.assertEqual(v.get_name(),
                             'Sensitive CORS methods enabled',
                             msg)

    def test_universal_allow_not(self):
        allow_methods = 'GET, POST, OPTIONS'
        allow_origin = 'http://w3af.org/'
        allow_credentials = 'false'

        self.co._analyze_server_response(self.request, self.url, self.origin,
                                         self.response, allow_origin,
                                         allow_credentials, allow_methods)
        vulns = self.kb.get('cors_origin', 'cors_origin')

        self.assertEqual(len(vulns), 0, vulns)

    def test_universal_allow_yes(self):
        allow_methods = 'GET, POST, OPTIONS'
        allow_origin = '*'
        allow_credentials = 'false'

        self.co._analyze_server_response(self.request, self.url, self.origin,
                                         self.response, allow_origin,
                                         allow_credentials, allow_methods)
        vulns = self.kb.get('cors_origin', 'cors_origin')

        self.assertEqual(len(vulns), 1, vulns)
        vuln = vulns[0]

        self.assertEqual(vuln.get_name(),
                         'Access-Control-Allow-Origin set to "*"')
        self.assertNotEqual(vuln.get_desc(), None)

    def test_universal_origin_echo_false(self):
        allow_methods = 'GET, POST, OPTIONS'
        allow_origin = 'http://www.google.com/'
        allow_credentials = 'false'
        self.co._analyze_server_response(self.request, self.url, self.origin,
                                         self.response, allow_origin,
                                         allow_credentials, allow_methods)
        vulns = self.kb.get('cors_origin', 'cors_origin')

        self.assertEqual(len(vulns), 0, vulns)

    def test_universal_origin_echo_without_credentials(self):
        allow_methods = 'GET, POST, OPTIONS'
        allow_origin = 'http://moth/'
        allow_credentials = 'false'
        self.co._analyze_server_response( self.request, self.url, self.origin,
                                          self.response, allow_origin,
                                          allow_credentials, allow_methods)
        vulns = self.kb.get('cors_origin', 'cors_origin')

        self.assertEqual(len(vulns), 1, vulns)
        vuln = vulns[0]

        self.assertEqual(vuln.get_name(),
                         'Insecure Access-Control-Allow-Origin')
        self.assertNotEqual(vuln.get_desc(), None)

    def test_universal_origin_echo_with_credentials(self):
        allow_methods = 'GET, POST, OPTIONS'
        allow_origin = 'http://moth/'
        allow_credentials = 'true'
        self.co._analyze_server_response(self.request, self.url, self.origin,
                                         self.response, allow_origin,
                                         allow_credentials, allow_methods)
        vulns = self.kb.get('cors_origin', 'cors_origin')

        self.assertEqual(len(vulns), 1, vulns)
        vuln = vulns[0]

        self.assertEqual(vuln.get_name(),
                         'Insecure Access-Control-Allow-Origin with credentials')
        self.assertNotEqual(vuln.get_desc(), None)

    def test_universal_origin_allow_creds(self):
        allow_methods = 'GET, POST, OPTIONS'
        allow_origin = '*'
        allow_credentials = 'true'
        self.co._analyze_server_response(self.request, self.url, self.origin,
                                         self.response, allow_origin,
                                         allow_credentials, allow_methods)
        vulns = self.kb.get('cors_origin', 'cors_origin')
        self.assertEqual(len(vulns), 2, vulns)

        name_creds = 'Incorrect withCredentials implementation'
        acao_star = 'Access-Control-Allow-Origin set to "*"'

        impl_err_vuln = [v for v in vulns if v.get_name() == name_creds]
        acao_all_vuln = [v for v in vulns if v.get_name() == acao_star]

        vuln = impl_err_vuln[0]
        self.assertEqual(vuln.get_name(),
                         'Incorrect withCredentials implementation')
        self.assertNotEqual(vuln.get_desc(), None)

        vuln = acao_all_vuln[0]
        self.assertEqual(vuln.get_name(),
                         'Access-Control-Allow-Origin set to "*"')
        self.assertNotEqual(vuln.get_desc(), None)