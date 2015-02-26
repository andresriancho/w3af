"""
test_cross_domain_js.py

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

from nose.plugins.attrib import attr

import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.misc.temp_dir import create_temp_dir

from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.plugins.grep.cross_domain_js import cross_domain_js


@attr('smoke')
class TestCrossDomainJS(PluginTest):

    target_url = get_moth_http('/grep/cross_domain_js/')

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('cross_domain_js'),),
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL)),)
            }
        }
    }

    def test_found_vuln(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        infos = self.kb.get('cross_domain_js', 'cross_domain_js')
        self.assertEquals(3, len(infos), infos)

        EXPECTED = {'cross_domain_script_mixed.html',
                    'cross_domain_script_with_type.html',
                    'cross_domain_script.html'}
        found_fnames = set([i.get_url().get_file_name() for i in infos])

        self.assertEquals(EXPECTED,
                          found_fnames)


class TestCrossDomainJSRaw(unittest.TestCase):

    def setUp(self):
        create_temp_dir()
        kb.kb.cleanup()
        self.plugin = cross_domain_js()

    def tearDown(self):
        kb.kb.cleanup()

    def test_cross_domain_third_party_is_secure(self):
        body = '<script src="https://cdn.akamai.net/foo.js"></script>'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=1)

        self.plugin.grep(request, resp)
        self.plugin.end()

        infos = kb.kb.get('cross_domain_js', 'cross_domain_js')
        self.assertEquals(len(infos), 0)

    def test_cross_domain_third_party_is_insecure(self):
        body = '<script src="https://cdn.akamai-wannabe.net/foo.js"></script>'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=1)

        self.plugin.grep(request, resp)
        self.plugin.end()

        infos = kb.kb.get('cross_domain_js', 'cross_domain_js')
        self.assertEquals(len(infos), 1)