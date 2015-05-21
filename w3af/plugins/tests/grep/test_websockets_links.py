"""
test_websockets_links.py

Copyright 2011 Andres Riancho

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
from w3af.plugins.grep.websockets_links import websockets_links
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL


class TestWebsocketsLinks(unittest.TestCase):

    def setUp(self):
        self.plugin = websockets_links()
        kb.kb.clear('websockets_links', 'websockets_links')

    def tearDown(self):
        self.plugin.end()

    def test_sl_1(self, *args):
        """
        Static link 1, ws link in the second tag
        """
        body = 'header<script>alert("first tag without ws!)</script>' \
               '<div><pre>wss://</pre></div>' \
               '<script>ws = ' \
               'new WebSocket("ws://www.example.com:8080/socketserver");' \
               '</script>footer'
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(kb.kb.get('websockets_links',
                                       'websockets_links')), 1)

    def test_sl_2(self, *args):
        """
        Static link 2, report two different InfoSets, one for each URL
        """
        body = 'header<script>' \
               'ws1 = ' \
               'new WebSocket("ws://www.example.com/socketserver");' \
               'ws2 = '\
               'new WebSocket("wss://SECURESOCKETSERVER:8080");' \
               '</script>'
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(kb.kb.get('websockets_links',
                                       'websockets_links')), 2)

    def test_sl_3(self, *args):
        """
        Static link 3, text/javascript
        """
        body = 'function { ws_url =' \
               '"wss://www.example.com/socketserver:8080";' \
               'wslink = new WebSocket(url); return wslink} '
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/javascript')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(kb.kb.get('websockets_links',
                                       'websockets_links')), 1)

    def test_dl_1(self, *args):
        """
        ws link is dynamically created
        """
        body = """header<script>new WebSocket(url("data"))
                function url(s) {
                var l = window.location;
                return ((l.protocol === "https:") ? "wss://" : "ws://") +
                l.hostname + (((l.port != 80) &&
                (l.port != 443)) ? ":" + l.port : "") +
                l.pathname + s;}</script>footer"""
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(kb.kb.get('websockets_links',
                                       'websockets_links')), 0)

    def test_fl_1(self, *args):
        """
        False links, must not be detected
        """
        body = """header<div class="postmsg">
               <div class="post_body_html">
               <pre>ws://www.example.com:8080/socketserver</pre>
               <pre>'ws://www.example.com/socketserver'</pre>
               </div>footer"""
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(kb.kb.get('websockets_links',
                                       'websockets_links')), 0)

    def test_no_link(self, *args):
        """
        No websockets link
        """
        body = """header<div class="nolink"></div>footer"""
        url = URL('https://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEqual(len(kb.kb.get('websockets_links',
                                       'websockets_links')), 0)

    def test_static_link_group_by_ws_url(self, *args):
        """
        Find the WS url, create an InfoSet and if others are found then add
        the knowledge to the existing InfoSet. Avoids multiple reports of the
        same WS url.
        """
        body = 'header' \
               '<script>ws = ' \
               'new WebSocket("ws://www.example.com:8080/socketserver");' \
               '</script>footer'

        url = URL('https://www.w3af.com/1')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        url = URL('https://www.w3af.com/2')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=2)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)

        ws_info_sets = kb.kb.get('websockets_links', 'websockets_links')
        self.assertEqual(len(ws_info_sets), 1)

        info_set = ws_info_sets[0]
        expected_desc = u'The application uses the HTML5 WebSocket URL' \
                        u' "ws://www.example.com:8080/socketserver" in' \
                        u' 2 different URLs. The first ten URLs are:\n' \
                        u' - https://www.w3af.com/1\n' \
                        u' - https://www.w3af.com/2\n'
        self.assertEqual(len(info_set.infos), 2)
        self.assertEqual(info_set.get_id(), [1, 2])
        self.assertEqual(info_set.get_desc(), expected_desc)