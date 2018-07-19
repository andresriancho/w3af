"""
test_credit_cards.py

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
import os
import unittest

import w3af.core.data.kb.knowledge_base as kb

from w3af import ROOT_PATH
from w3af.plugins.grep.credit_cards import credit_cards
from w3af.core.data.dc.headers import Headers
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL


class TestCreditCards(unittest.TestCase):

    def setUp(self):
        self.plugin = credit_cards()
        kb.kb.clear('credit_cards', 'credit_cards')

    def tearDown(self):
        self.plugin.end()

    def test_find_credit_card(self):
        body = '378282246310005'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('credit_cards', 'credit_cards')), 1)

    def test_find_credit_card_spaces(self):
        body = '3566 0020 2036 0505'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('credit_cards', 'credit_cards')), 1)

    def test_find_credit_card_html(self):
        body = '<a> 378282246310005</a>'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('credit_cards', 'credit_cards')), 1)

    def test_not_find_credit_cards(self):
        invalid_cards = ('b71449635402848',  # Start with a letter
                         '356 600 20203605 05',
                         # Spaces in incorrect locations
                         '35660020203605054',  # Extra number added at the end
                         '13566002020360505',
                         # Extra number added at the beginning
                         # Not a credit card at all
                         '_c3E6E547C-BFB7-4897-86EA-882A04BDE274_kDF867BE9-DEC5-0FFF-6629-127552370B17',
                         )
        for card in invalid_cards:
            body = '<A href="#123">%s</A>' % card
            url = URL('http://www.w3af.com/')
            headers = Headers([('content-type', 'text/html')])
            response = HTTPResponse(200, body, headers, url, url, _id=1)
            request = FuzzableRequest(url, method='GET')
            self.plugin.grep(request, response)
            self.assertEquals(
                len(kb.kb.get('credit_cards', 'credit_cards')), 0)
            kb.kb.clear('credit_cards', 'credit_cards')

    def test_invalid_check_not_find_credit_card_spaces(self):
        body = '3566 0020 2036 0705'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, body, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')
        self.plugin.grep(request, response)
        self.assertEquals(len(kb.kb.get('credit_cards', 'credit_cards')), 0)

    def test_find_credit_card_performance_true(self):
        credit_card = '3566 0020 2036 0505'

        html_file = os.path.join(ROOT_PATH, 'plugins/tests/grep/data/test-3.html')
        html = file(html_file).read()
        html = html[:len(html) / 2] + ' ' + credit_card + ' ' + html[len(html) / 2:]

        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        response = HTTPResponse(200, html, headers, url, url, _id=1)
        request = FuzzableRequest(url, method='GET')

        for _ in xrange(5000):
            self.plugin.grep(request, response)

        self.assertEquals(len(kb.kb.get('credit_cards', 'credit_cards')), 1)
