# -*- coding: utf-8 -*-
'''
test_httpResponse.py

Copyright 2011 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

import unittest
import codecs

from ..httpResponse import httpResponse, DEFAULT_CHARSET, _returnEscapedChar
from core.data.parsers.urlParser import url_object

codecs.register_error('default', _returnEscapedChar)

TEST_RESPONSES = {
    'hebrew': (u'ולהכיר טוב יותר את המוסכמות, האופי', 'Windows-1255'),
    'japanese': (u'頴英 衛詠鋭液疫 益駅悦謁越榎厭円', 'EUC-JP'),
    'russian': (u'Вы действительно хотите удалить? Данное действие', 'Windows-1251'),
    'hungarian': (u'Üdvözöljük a SZTAKI webkeresőjében', 'ISO-8859-2'),
    'greek': (u'Παρακαλούμε πριν προχωρήσετε καταχώρηση', 'ISO-8859-7'),
}


class TestHTTPResponse(unittest.TestCase):
    
    def setUp(self):
        self.resp = self.create_resp({'Content-Type': 'text/html'})
    
    def create_resp(self, headers, body=u'body'):
        url = url_object('http://w3af.com')
        return httpResponse(200, body, headers, url, url)
    
    def test_unicode_body_no_charset(self):
        '''
        A charset *must* be passed as arg when creating a new
        httpResponse; otherwise expect an error.
        '''
        self.assertRaises(AssertionError, self.resp.getBody)
    
    def test_rawread_is_none(self):
        '''
        Guarantee that the '_raw_body' attr is set to None after
        used (Memory optimization)
        '''
        resp = self.resp
        resp.setCharset('utf-8')
        # Use the 'raw body'
        _ = resp.getBody()
        self.assertEquals(resp._raw_body, None)
    
    def test_doc_type(self):
        
        # Text or HTML
        text_or_html_mime_types = (
            'application/javascript', 'text/html', 'text/xml', 'text/cmd',
            'text/css', 'text/csv', 'text/javascript', 'text/plain'
            )
        for mimetype in text_or_html_mime_types:
            resp = self.create_resp({'Content-Type': mimetype})
            self.assertEquals(
                True, resp.is_text_or_html(),
                "MIME type '%s' wasn't recognized as a valid '%s' type"
                % (mimetype, httpResponse.DOC_TYPE_TEXT_OR_HTML)
            )
        
        # PDF
        resp = self.create_resp({'Content-Type': 'application/pdf'})
        self.assertEquals(True, resp.is_pdf())
        
        # SWF
        resp = self.create_resp({'Content-Type': 'application/x-shockwave-flash'})
        self.assertEquals(True, resp.is_swf())
        
        # Image
        image_mime_types = (
            'image/gif', 'image/jpeg', 'image/pjpeg', 'image/png','image/tiff',
            'image/svg+xml', 'image/vnd.microsoft.icon'
            )
        for mimetype in image_mime_types:
            resp = self.create_resp({'Content-Type': mimetype})
            self.assertEquals(
                True, resp.is_image(),
                "MIME type '%s' wasn't recognized as a valid '%s' type"
                % (mimetype, httpResponse.DOC_TYPE_IMAGE)
            )
    
    def test_parse_response_with_charset_in_both_headers(self):
        # Ensure that the responses' bodies are correctly decoded (charset in 
        # both the http and html). Only http charset is expected to be used.
        for body, charset in TEST_RESPONSES.values():
            hvalue = 'text/html; charset=%s' % charset
            body = ('<meta http-equiv=Content-Type content="text/html;'
                    'charset=utf-16"/>' + body)
            htmlbody = '%s' % body.encode(charset)
            resp = self.create_resp({'content-type': hvalue}, htmlbody)
            self.assertEquals(body, resp.getBody())
    
    def test_parse_response_with_charset_in_meta_header(self):
        # Ensure responses' bodies are correctly decoded (charset only
        # in the html meta header)
        for body, charset in TEST_RESPONSES.values():
            body = ('<meta http-equiv=Content-Type content="text/html;'
                    'charset=%s/>' % charset)
            htmlbody = '%s' % body.encode(charset)
            resp = self.create_resp({}, htmlbody)
            self.assertEquals(body, resp.body)
    
    def test_parse_response_with_no_charset_in_header(self):
        # No charset was specified, use the default as well as the default
        # error handling scheme
        for body, charset in TEST_RESPONSES.values():
            html = body.encode(charset)
            resp = self.create_resp({'Content-Type':'text/xml'}, html)
            self.assertEquals(html.decode(DEFAULT_CHARSET, 'default'), resp.body)
    
    def test_parse_response_with_wrong_charset(self):
        # A wrong or non-existant charset was set; try to decode the response
        # using the default charset and handling scheme
        from random import choice
        for body, charset in TEST_RESPONSES.values():
            html = body.encode(charset)
            headers = {'Content-Type': 'text/xml; charset=%s' % 
                                            choice(('XXX', 'utf-8'))}
            resp = self.create_resp(headers, html)
            self.assertEquals(html.decode(DEFAULT_CHARSET, 'default'), resp.body)
    
    def test_eval_xpath_in_dom(self):
        html = """
        <html>
          <head>
            <title>THE TITLE</title>
          </head>
          <body>
            <input name="user" type="text">
            <input name="pass" type="password">
          </body>
        </html>"""
        headers = {'Content-Type': 'text/xml'}
        resp = self.create_resp(headers, html)
        self.assertEquals(2, len(resp.getDOM().xpath('.//input')))
    
    def test_dom_are_the_same(self):
        resp = self.create_resp({'conten-type': 'text/html'}, "<html/>")
        domid = id(resp.getDOM())
        self.assertEquals(domid, id(resp.getDOM()))
    
    