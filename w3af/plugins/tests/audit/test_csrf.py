# -*- coding: utf-8 -*-
"""
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
"""
import unittest

from w3af.plugins.tests.helper import PluginTest, PluginConfig, LOREM
from w3af.plugins.audit.csrf import csrf
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.parsers.doc.url import URL, parse_qs
from w3af.core.data.parsers.utils.form_params import FormParameters
from w3af.core.data.dc.headers import Headers
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.dc.urlencoded_form import URLEncodedForm
from w3af.core.data.dc.cookie import Cookie
from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.controllers.ci.w3af_moth import get_w3af_moth_http


class TestCSRF(PluginTest):

    target_url = get_w3af_moth_http('/w3af/audit/csrf/')

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

    def test_found_csrf(self):
        expected = [
            '/w3af/audit/csrf/vulnerable/buy.php',
            '/w3af/audit/csrf/vulnerable-rnd/buy.php',
            '/w3af/audit/csrf/link-vote/vote.php',

            # See https://github.com/andresriancho/w3af/issues/120
            # '/w3af/audit/csrf/vulnerable-token-ignored/buy.php',
        ]
        
        # Run the scan
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('csrf', 'csrf')
        
        self.assertEquals(set(expected),
                          set([v.get_url().get_path() for v in vulns]))
        self.assertTrue(
            all(['CSRF vulnerability' == v.get_name() for v in vulns]))

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
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])

        res = HTTPResponse(200, 'body', headers, url, url)

        # False because no cookie is set and no QS nor post-data
        url = URL('http://moth/')
        req = FuzzableRequest(url, method='GET')
        suitable = self.csrf_plugin._is_suitable(req, res)
        self.assertFalse(suitable)

        # False because no cookie is set
        url = URL('http://moth/?id=3')
        req = FuzzableRequest(url, method='GET')
        suitable = self.csrf_plugin._is_suitable(req, res)
        self.assertFalse(suitable)

        url_sends_cookie = URL(get_w3af_moth_http('/w3af/core/cookie_handler/set-cookie.php'))
        self.uri_opener.GET(url_sends_cookie)
        
        # Still false because it doesn't have any QS or POST data
        url = URL('http://moth/')
        req = FuzzableRequest(url, method='GET')
        suitable = self.csrf_plugin._is_suitable(req, res)
        self.assertFalse(suitable)

        self.csrf_plugin._strict_mode = True

        # Still false because of the strict mode
        url = URL('http://moth/?id=3')
        req = FuzzableRequest(url, method='GET')
        suitable = self.csrf_plugin._is_suitable(req, res)
        self.assertFalse(suitable)

        # False, no items in post-data
        url = URL('http://moth/')
        req = FuzzableRequest(url, method='POST', post_data=URLEncodedForm())
        suitable = self.csrf_plugin._is_suitable(req, res)
        self.assertFalse(suitable)

        # True, items in DC, POST (passes strict mode) and cookies
        url = URL('http://moth/')
        form_params = FormParameters()
        form_params.add_field_by_attr_items([('name', 'test'), ('type', 'text')])
        form = URLEncodedForm(form_params)
        req = FuzzableRequest(url, method='POST', post_data=form)
        suitable = self.csrf_plugin._is_suitable(req, res)
        self.assertTrue(suitable)
        
        self.csrf_plugin._strict_mode = False

        # True now that we have strict mode off, cookies and QS
        url = URL('http://moth/?id=3')
        req = FuzzableRequest(url, method='GET')
        suitable = self.csrf_plugin._is_suitable(req, res)
        self.assertTrue(suitable)

    def test_is_origin_checked_true_case01(self):
        url = URL(get_w3af_moth_http('/w3af/audit/csrf/referer/buy.php?shares=123'))
        headers = Headers([('Referer', 'http://moth/w3af/audit/csrf/referer/')])
        freq = FuzzableRequest(url, method='GET', headers=headers)
        
        orig_response = self.uri_opener.send_mutant(freq)
        
        origin_checked = self.csrf_plugin._is_origin_checked(freq, orig_response, None)
        self.assertTrue(origin_checked)

    def test_is_origin_checked_true_case02(self):
        url = URL(get_w3af_moth_http('/w3af/audit/csrf/referer-rnd/buy.php?shares=123'))
        headers = Headers([('Referer', 'http://moth/w3af/audit/csrf/referer-rnd/')])
        freq = FuzzableRequest(url, method='GET', headers=headers)
        
        orig_response = self.uri_opener.send_mutant(freq)
        
        origin_checked = self.csrf_plugin._is_origin_checked(freq, orig_response, None)
        self.assertTrue(origin_checked)

    def test_is_origin_checked_false(self):
        url = URL(get_w3af_moth_http('/w3af/audit/csrf/vulnerable/buy.php?shares=123'))
        headers = Headers([('Referer', 'http://moth/w3af/audit/csrf/referer-rnd/')])
        freq = FuzzableRequest(url, method='GET', headers=headers)
        
        orig_response = self.uri_opener.send_mutant(freq)
        
        origin_checked = self.csrf_plugin._is_origin_checked(freq, orig_response, None)
        self.assertFalse(origin_checked)

    def test_is_token_checked_true(self):
        generator = URL(get_w3af_moth_http('/w3af/audit/csrf/secure-replay-allowed/'))
        http_response = self.uri_opener.GET(generator)

        # Please note that this freq holds a fresh/valid CSRF token
        cookie = Cookie.from_http_response(http_response)
        freq = FuzzableRequest(generator, cookie=cookie)

        # FIXME:
        # And I use this token here to get the original response, and if the
        # application is properly developed, that token will be invalidated
        # and that's where this algorithm fails.
        original_response = self.uri_opener.send_mutant(freq)

        token = {'token': 'cc2544ba4af772c31bc3da928e4e33a8'}
        checked = self.csrf_plugin._is_token_checked(freq, token,
                                                     original_response)
        self.assertTrue(checked)

    def test_is_token_checked_false(self):
        """
        This covers the case where there is a token but for some reason it
        is NOT verified by the web application.
        """
        generator = URL(get_w3af_moth_http('/w3af/audit/csrf/vulnerable-token-ignored/'))
        http_response = self.uri_opener.GET(generator)

        # Please note that this freq holds a fresh/valid CSRF token
        cookie = Cookie.from_http_response(http_response)
        freq = FuzzableRequest(generator, cookie=cookie)

        # FIXME:
        # And I use this token here to get the original response, and if the
        # application is properly developed, that token will be invalidated
        # and that's where this algorithm fails.
        original_response = self.uri_opener.send_mutant(freq)

        token = {'token': 'cc2544ba4af772c31bc3da928e4e33a8'}
        checked = self.csrf_plugin._is_token_checked(freq, token, original_response)
        self.assertFalse(checked)


class TestLowLevelCSRF(unittest.TestCase):
    def setUp(self):
        super(TestLowLevelCSRF, self).setUp()
        self.csrf_plugin = csrf()

    def test_is_csrf_token_true_case01(self):
        self.assertTrue(self.csrf_plugin.is_csrf_token('token', 'f842eb01b87a8ee18868d3bf80a558f3'))

    def test_is_csrf_token_true_case02(self):
        self.assertTrue(self.csrf_plugin.is_csrf_token('secret', 'f842eb01b87a8ee18868d3bf80a558f3'))

    def test_is_csrf_token_true_case03(self):
        self.assertTrue(self.csrf_plugin.is_csrf_token('csrf', 'f842eb01b87a8ee18868d3bf80a558f3'))

    def test_is_csrf_token_false_case01(self):
        self.assertFalse(self.csrf_plugin.is_csrf_token('token', ''))
    
    def test_is_csrf_token_false_case02(self):
        self.assertFalse(self.csrf_plugin.is_csrf_token('secret', 'helloworld'))

    def test_is_csrf_token_false_case03(self):
        self.assertFalse(self.csrf_plugin.is_csrf_token('secret', 'helloworld123'))

    def test_is_csrf_token_false_case04(self):
        self.assertFalse(self.csrf_plugin.is_csrf_token('secret', 'hello world 123'))

    def test_is_csrf_token_false_long(self):
        self.assertFalse(self.csrf_plugin.is_csrf_token('secret', 'A' * 513))

    def test_is_csrf_token_false_string_special_chars(self):
        self.assertFalse(self.csrf_plugin.is_csrf_token('secret', 'áÄé'))

    def test_is_csrf_token_false_unicode(self):
        self.assertFalse(self.csrf_plugin.is_csrf_token('secret', u'áÄé'))

    def test_is_csrf_token_false_case05(self):
        self.assertTrue(self.csrf_plugin.is_csrf_token('secret', LOREM))

    def test_is_csrf_token_false_case06(self):
        self.assertFalse(self.csrf_plugin.is_csrf_token('token', 'f842e'))

    def test_find_csrf_token_true_simple(self):
        url = URL('http://moth/w3af/audit/csrf/')
        query_string = parse_qs('secret=f842eb01b87a8ee18868d3bf80a558f3')
        freq = FuzzableRequest(url, method='GET')
        freq.set_querystring(query_string)
        
        token = self.csrf_plugin._find_csrf_token(freq)
        self.assertIn('secret', token)

    def test_find_csrf_token_true_repeated(self):
        url = URL('http://moth/w3af/audit/csrf/')
        query_string = parse_qs('secret=f842eb01b87a8ee18868d3bf80a558f3'
                                '&secret=not a token')
        freq = FuzzableRequest(url, method='GET')
        freq.set_querystring(query_string)

        token = self.csrf_plugin._find_csrf_token(freq)
        self.assertIn('secret', token)

    def test_find_csrf_token_false(self):
        url = URL('http://moth/w3af/audit/csrf/')
        query_string = parse_qs('secret=not a token')
        freq = FuzzableRequest(url, method='GET')
        freq.set_querystring(query_string)
        
        token = self.csrf_plugin._find_csrf_token(freq)
        self.assertIn('secret', token)
