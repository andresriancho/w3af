"""
test_strange_reason.py

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
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.plugins.grep.strange_reason import strange_reason


class TestStrangeReason(unittest.TestCase):

    def setUp(self):
        kb.kb.cleanup()
        self.plugin = strange_reason()
        self.url = URL('http://www.w3af.com/')
        self.headers = Headers([('content-type', 'text/html')])
        self.request = FuzzableRequest(self.url)

    def tearDown(self):
        self.plugin.end()

    def test_strange_reason_empty(self):
        response = HTTPResponse(200, '', self.headers, self.url, self.url,
                                _id=1, msg='Ok')
        self.plugin.grep(self.request, response)
        self.assertEquals(len(kb.kb.get('strange_reason', 'strange_reason')), 0)

    def test_strange_reason_large(self):
        response = HTTPResponse(300, 'A' * 4096, self.headers, self.url,
                                self.url, _id=1, msg='Multiple Choices')
        self.plugin.grep(self.request, response)
        self.assertEquals(len(kb.kb.get('strange_reason', 'strange_reason')), 0)

    def test_strange_reason_found_200(self):
        response = HTTPResponse(200, 'A' * 4096, self.headers, self.url,
                                self.url, _id=1, msg='Foo!')
        self.plugin.grep(self.request, response)
        self.assertEquals(len(kb.kb.get('strange_reason', 'strange_reason')), 1)

    def test_strange_reason_found_300(self):
        response = HTTPResponse(300, 'A' * 2 ** 10, self.headers,
                                self.url, self.url, _id=1, msg='Multiple')
        self.plugin.grep(self.request, response)
        self.assertEquals(len(kb.kb.get('strange_reason', 'strange_reason')), 1)

    def test_group_by_reason(self):
        response = HTTPResponse(200, '', self.headers, self.url, self.url,
                                _id=1, msg='Foos')
        self.plugin.grep(self.request, response)

        response = HTTPResponse(200, '', self.headers, self.url, self.url,
                                _id=3, msg='Foos')
        self.plugin.grep(self.request, response)

        info_sets = kb.kb.get('strange_reason', 'strange_reason')
        self.assertEquals(len(info_sets), 1)

        expected_desc = u'The remote web server sent 1 HTTP responses with ' \
                        u'the uncommon status message "Foos", manual ' \
                        u'inspection is recommended. The first ten URLs ' \
                        u'which sent the uncommon message are:\n' \
                        u' - http://www.w3af.com/\n'
        info_set = info_sets[0]
        self.assertEqual(info_set.get_id(), [1, 3])
        self.assertEqual(info_set.get_desc(), expected_desc)

    def test_no_group_by_different_reason(self):
        response = HTTPResponse(200, '', self.headers, self.url, self.url,
                                _id=1, msg='Foo')
        self.plugin.grep(self.request, response)

        response = HTTPResponse(200, '', self.headers, self.url, self.url,
                                _id=3, msg='Bar')
        self.plugin.grep(self.request, response)

        info_sets = kb.kb.get('strange_reason', 'strange_reason')
        self.assertEquals(len(info_sets), 2)
