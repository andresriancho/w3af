"""
test_error_pages.py

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

import w3af.core.data.constants.severity as severity
import w3af.core.data.kb.knowledge_base as kb

from w3af.plugins.grep.error_pages import error_pages
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig


@attr('ci_ready')
@attr('smoke')
class TestErrorPages(PluginTest):

    target_url = get_moth_http('/grep/error_pages/index.html')

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('error_pages'),)
            }
        }
    }

    def test_found_vuln(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        infos = self.kb.get('error_pages', 'error_page')
        self.assertEquals(1, len(infos))
        info = infos[0]

        self.assertEquals(1, len(infos), infos)
        self.assertEquals(self.target_url, str(info.get_url()))
        self.assertEquals(severity.INFORMATION, info.get_severity())
        self.assertTrue(info.get_name().startswith('Descriptive error page'))

    def setUp(self):
        super(TestErrorPages, self).setUp()
        kb.kb.cleanup()

    def test_found_vuln_max_reports(self):
        kb.kb.cleanup()
        plugin = error_pages()

        body = plugin.ERROR_PAGES[5]
        headers = Headers({'content-type': 'text/html'}.items())

        for i in xrange(plugin.MAX_REPORTED_PER_MSG * 2):
            url = URL('http://www.w3af.com/%s' % i)
            request = FuzzableRequest(url, method='GET')
            response = HTTPResponse(200, body, headers, url, url, _id=1)

            plugin.grep(request, response)

        plugin.end()

        self.assertEqual(len(kb.kb.get('error_pages', 'error_page')),
                         plugin.MAX_REPORTED_PER_MSG + 1)

    def test_found_vuln_max_reports_two_different(self):
        kb.kb.cleanup()
        plugin = error_pages()

        body = plugin.ERROR_PAGES[5]
        headers = Headers({'content-type': 'text/html'}.items())

        for i in xrange(plugin.MAX_REPORTED_PER_MSG * 2):
            url = URL('http://www.w3af.com/%s' % i)
            request = FuzzableRequest(url, method='GET')
            response = HTTPResponse(200, body, headers, url, url, _id=1)

            plugin.grep(request, response)

        # Note that here I chose a different error message
        body = plugin.ERROR_PAGES[7]
        url = URL('http://www.w3af.com/iamdifferent')
        request = FuzzableRequest(url, method='GET')
        response = HTTPResponse(200, body, headers, url, url, _id=1)

        plugin.grep(request, response)

        plugin.end()

        self.assertEqual(len(kb.kb.get('error_pages', 'error_page')),
                         plugin.MAX_REPORTED_PER_MSG + 2)