"""
test_path_disclosure.py

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

import w3af.core.data.kb.knowledge_base as kb

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.data.url.HTTPResponse import HTTPResponse as HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest as FuzzableRequest
from w3af.plugins.grep.path_disclosure import path_disclosure


class TestPathDisclosure(unittest.TestCase):

    def setUp(self):
        kb.kb.cleanup()
        
        self.plugin = path_disclosure()
        self.url = URL('http://www.w3af.com/foo/bar.py')
        self.header = Headers([('content-type', 'text/html')])
        self.request = FuzzableRequest(self.url, method='GET')

    def tearDown(self):
        self.plugin.end()
        kb.kb.cleanup()

    def _create_response(self, body):
        return HTTPResponse(200, body, self.header, self.url, self.url, _id=1)

    def test_path_disclosure(self):
        res = self._create_response('header body footer')
        self.plugin.grep(self.request, res)
        infos = kb.kb.get('path_disclosure', 'path_disclosure')
        self.assertEquals(len(infos), 0)

    def test_path_disclosure_positive(self):
        res = self._create_response('header /etc/passwd footer')
        self.plugin.grep(self.request, res)

        infos = kb.kb.get('path_disclosure', 'path_disclosure')
        self.assertEquals(len(infos), 1)

        path = infos[0]['path']
        self.assertEqual(path, '/etc/passwd')

    def test_path_disclosure_false_positive_6640(self):
        # see: https://github.com/andresriancho/w3af/issues/6640
        path = '/media/js/spotlight.js'
        kb.kb.add_url(URL('http://mock%s' % path))

        res = self._create_response('header %s footer' % path)
        self.plugin.grep(self.request, res)

        infos = kb.kb.get('path_disclosure', 'path_disclosure')
        self.assertEquals(len(infos), 0)

    def test_path_disclosure_calculated_webroot(self):
        kb.kb.add_url(self.url)

        res = self._create_response('header /var/www/foo/bar.py footer')
        self.plugin.grep(self.request, res)

        webroot = kb.kb.raw_read('path_disclosure', 'webroot')
        self.assertEqual(webroot, '/var/www')

    def test_path_disclosure_false_positive_in_tag_attr(self):
        kb.kb.add_url(self.url)

        res = self._create_response('nope <a href="/var/www/foo/bar.py">x</a>')
        self.plugin.grep(self.request, res)

        infos = kb.kb.get('path_disclosure', 'path_disclosure')
        self.assertEquals(len(infos), 0)

    def test_path_disclosure_false_positive_not_starting_with(self):
        kb.kb.add_url(URL('http://mock/js/banner.js'))

        res = self._create_response('header /images/banners/home/internet.jpg footer')
        self.plugin.grep(self.request, res)

        infos = kb.kb.get('path_disclosure', 'path_disclosure')
        self.assertEquals(len(infos), 0)

    def test_path_disclosure_tag_text(self):
        kb.kb.add_url(self.url)

        res = self._create_response('<a ...>/var/www/foo/bar.py</a>')
        self.plugin.grep(self.request, res)

        infos = kb.kb.get('path_disclosure', 'path_disclosure')
        self.assertEquals(len(infos), 1)

    def test_path_disclosure_tag_text_quotes(self):
        kb.kb.add_url(self.url)

        res = self._create_response('<a ...>Error at "/var/www/foo/bar.py"</a>')
        self.plugin.grep(self.request, res)

        infos = kb.kb.get('path_disclosure', 'path_disclosure')
        self.assertEquals(len(infos), 1)
