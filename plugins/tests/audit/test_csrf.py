'''
test_csrf.py

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
'''
from plugins.tests.helper import PluginTest, PluginConfig
from nose.plugins.skip import SkipTest

from plugins.audit.csrf import csrf

from core.data.url.HTTPResponse import HTTPResponse
from core.data.parsers.url import URL
from core.data.dc.headers import Headers
from core.data.request.fuzzable_request import FuzzableRequest
from core.data.dc.form import Form
from core.data.parsers.url import parse_qs
from core.data.url.extended_urllib import ExtendedUrllib


class TestCSRF(PluginTest):

    target_url = 'http://moth/w3af/audit/csrf/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (PluginConfig('csrf'),),
                'crawl': (
                    PluginConfig(
                        'web_spider',
                        ('only_forward', True, PluginConfig.BOOL)),
                )
            }
        }
    }

    def setUp(self):
        super(TestCSRF, self).setUp()
        
        self.csrf_plugin = csrf()
        self.uri_opener = ExtendedUrllib()
        self.csrf_plugin.set_url_opener(self.uri_opener)

    def test_resp_is_equal(self):
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])

        r1 = HTTPResponse(200, 'body', headers, url, url)
        r2 = HTTPResponse(404, 'body', headers, url, url)
        self.assertFalse(self.csrf_plugin._is_resp_equal(r1, r2))

        r1 = HTTPResponse(200, 'a', headers, url, url)
        r2 = HTTPResponse(200, 'b', headers, url, url)
        self.assertFalse(self.csrf_plugin._is_resp_equal(r1, r2))

        r1 = HTTPResponse(200, 'a', headers, url, url)
        r2 = HTTPResponse(200, 'a', headers, url, url)
        self.assertTrue(self.csrf_plugin._is_resp_equal(r1, r2))

    def test_is_suitable(self):
        # False because no cookie is set and no QS nor post-data
        url = URL('http://moth/')
        req = FuzzableRequest(url, method='GET')
        suitable = self.csrf_plugin._is_suitable(req)
        self.assertFalse(suitable)

        # False because no cookie is set
        url = URL('http://moth/?id=3')
        req = FuzzableRequest(url, method='GET')
        suitable = self.csrf_plugin._is_suitable(req)
        self.assertFalse(suitable)

        url_sends_cookie = URL(
            'http://moth/w3af/core/cookie_handler/set-cookie.php')
        self.uri_opener.GET(url_sends_cookie)
        
        # Still false because it doesn't have any QS or POST data
        url = URL('http://moth/')
        req = FuzzableRequest(url, method='GET')
        suitable = self.csrf_plugin._is_suitable(req)
        self.assertFalse(suitable)

        self.csrf_plugin._strict_mode = True

        # Still false because of the strict mode
        url = URL('http://moth/?id=3')
        req = FuzzableRequest(url, method='GET')
        suitable = self.csrf_plugin._is_suitable(req)
        self.assertFalse(suitable)

        # False, no items in dc
        url = URL('http://moth/')
        req = FuzzableRequest(url, method='POST', dc=Form())
        suitable = self.csrf_plugin._is_suitable(req)
        self.assertFalse(suitable)

        # True, items in DC, POST (passes strict mode) and cookies
        url = URL('http://moth/')
        form = Form()
        form.add_input([('name', 'test'), ('type', 'text')])
        req = FuzzableRequest(url, method='POST', dc=form)
        suitable = self.csrf_plugin._is_suitable(req)
        self.assertTrue(suitable)
        
        self.csrf_plugin._strict_mode = False

        # True now that we have strict mode off, cookies and QS
        url = URL('http://moth/?id=3')
        req = FuzzableRequest(url, method='GET')
        suitable = self.csrf_plugin._is_suitable(req)
        self.assertTrue(suitable)

    def test_is_origin_checked_true_case01(self):
        url = URL('http://moth/w3af/audit/csrf/referer/buy.php?shares=123')
        headers = Headers([('Referer', 'http://moth/w3af/audit/csrf/referer/')])
        freq = FuzzableRequest(url, method='GET', headers=headers)
        
        orig_response = self.uri_opener.send_mutant(freq)
        
        origin_checked = self.csrf_plugin._is_origin_checked(freq, orig_response)
        self.assertTrue(origin_checked)

    def test_is_origin_checked_true_case02(self):
        url = URL('http://moth/w3af/audit/csrf/referer-rnd/buy.php?shares=123')
        headers = Headers([('Referer', 'http://moth/w3af/audit/csrf/referer-rnd/')])
        freq = FuzzableRequest(url, method='GET', headers=headers)
        
        orig_response = self.uri_opener.send_mutant(freq)
        
        origin_checked = self.csrf_plugin._is_origin_checked(freq, orig_response)
        self.assertTrue(origin_checked)

    def test_is_origin_checked_false(self):
        url = URL('http://moth/w3af/audit/csrf/vulnerable/buy.php?shares=123')
        headers = Headers([('Referer', 'http://moth/w3af/audit/csrf/referer-rnd/')])
        freq = FuzzableRequest(url, method='GET', headers=headers)
        
        orig_response = self.uri_opener.send_mutant(freq)
        
        origin_checked = self.csrf_plugin._is_origin_checked(freq, orig_response)
        self.assertFalse(origin_checked)
    
    def test_is_csrf_token_true_case01(self):
        self.csrf_plugin.is_csrf_token('token', 'f842eb01b87a8ee18868d3bf80a558f3')

    def test_is_csrf_token_true_case02(self):
        self.csrf_plugin.is_csrf_token('secret', 'f842eb01b87a8ee18868d3bf80a558f3')

    def test_is_csrf_token_true_case03(self):
        self.csrf_plugin.is_csrf_token('csrf', 'f842eb01b87a8ee18868d3bf80a558f3')

    def test_is_csrf_token_false_case01(self):
        self.csrf_plugin.is_csrf_token('token', '')
    
    def test_is_csrf_token_false_case02(self):
        self.csrf_plugin.is_csrf_token('secret', 'helloworld')

    def test_is_csrf_token_false_case03(self):
        self.csrf_plugin.is_csrf_token('secret', 'helloworld123')

    def test_is_csrf_token_false_case04(self):
        self.csrf_plugin.is_csrf_token('secret', 'hello world 123')

    def test_is_csrf_token_false_case05(self):
        lorem = ('Lorem ipsum dolor sit amet, consectetur adipiscing elit.'
                 ' Curabitur at eros elit, rhoncus feugiat libero. Praesent'
                 ' lobortis ultricies est gravida tempor. Sed tortor mi,'
                 ' euismod at interdum quis, hendrerit vitae risus. Sed'
                 ' iaculis, ante sagittis ullamcorper molestie, metus nibh'
                 ' posuere purus, non tempor massa leo at odio. Duis quis'
                 ' elit enim. Morbi lobortis est sed metus adipiscing in'
                 ' lacinia est porttitor. Suspendisse potenti. Morbi pretium'
                 ' lacinia magna, sit amet tincidunt enim vestibulum sed.')
        self.csrf_plugin.is_csrf_token('secret', lorem)

    def test_is_csrf_token_false_case06(self):
        self.csrf_plugin.is_csrf_token('token', 'f842e')

    def test_find_csrf_token_true_simple(self):
        url = URL('http://moth/w3af/audit/csrf/')
        query_string = parse_qs('secret=f842eb01b87a8ee18868d3bf80a558f3')
        freq = FuzzableRequest(url, method='GET', dc=query_string)
        
        tokens = self.csrf_plugin._find_csrf_token(freq)
        self.assertIn('secret', tokens)

    def test_find_csrf_token_true_repeated(self):
        url = URL('http://moth/w3af/audit/csrf/')
        query_string = parse_qs('secret=f842eb01b87a8ee18868d3bf80a558f3'
                                '&secret=not a token')
        freq = FuzzableRequest(url, method='GET', dc=query_string)
        
        tokens = self.csrf_plugin._find_csrf_token(freq)
        self.assertIn('secret', tokens)

    def test_find_csrf_token_false(self):
        url = URL('http://moth/w3af/audit/csrf/')
        query_string = parse_qs('secret=not a token')
        freq = FuzzableRequest(url, method='GET', dc=query_string)
        
        tokens = self.csrf_plugin._find_csrf_token(freq)
        self.assertNotIn('secret', tokens)
        
    def test_found_csrf(self):
        raise SkipTest('Still need to work on this in order to make it work')

        # Run the scan
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('csrf', 'csrf')
        self.assertEquals(2, len(vulns))

        EXPECTED = [
            ('vulnerable/buy.php'),
            ('vulnerable-rnd/buy.php'),
        ]

        self.assertEquals(set(EXPECTED),
                          set([v.get_url().get_file_name() for v in vulns]))
        self.assertTrue(
            all(['CSRF vulnerability' == v.get_name() for v in vulns]))
