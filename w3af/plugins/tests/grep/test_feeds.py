"""
test_feeds.py

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
from w3af.plugins.grep.feeds import feeds
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers


class test_feeds(unittest.TestCase):

    def setUp(self):
        self.plugin = feeds()
        kb.kb.clear('feeds', 'feeds')

    def tearDown(self):
        self.plugin.end()

    def test_rss(self):
        body = 'header <rss version="3"> footer'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        self.assertEquals(len(kb.kb.get('feeds', 'feeds')), 1)
        i = kb.kb.get('feeds', 'feeds')[0]
        self.assertTrue('RSS' in i.get_desc())
        self.assertTrue('3' in i.get_desc())

    def test_feed(self):
        body = 'header <feed foo="4" version="3"> footer'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        self.assertEquals(len(kb.kb.get('feeds', 'feeds')), 1)
        i = kb.kb.get('feeds', 'feeds')[0]
        self.assertTrue('OPML' in i.get_desc())
        self.assertTrue('3' in i.get_desc())

    def test_opml(self):
        body = 'header <opml version="3" foo="4"> footer'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        self.assertEquals(len(kb.kb.get('feeds', 'feeds')), 1)
        i = kb.kb.get('feeds', 'feeds')[0]
        self.assertTrue('OPML' in i.get_desc())
        self.assertTrue('3' in i.get_desc())

    def test_no_feeds(self):
        body = 'header <nofeed version="3" foo="4"> footer'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        self.assertEquals(len(kb.kb.get('feeds', 'feeds')), 0)

    def test_no_version(self):
        body = 'header <rss foo="3"> footer'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        self.assertEquals(len(kb.kb.get('feeds', 'feeds')), 1)
        i = kb.kb.get('feeds', 'feeds')[0]
        self.assertTrue('RSS' in i.get_desc())
        self.assertTrue('unknown' in i.get_desc())
