# -*- coding: UTF-8 -*-
"""
test_get_clean_body.py

Copyright 2017 Andres Riancho

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
from __future__ import division

import unittest

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.core_helpers.not_found.get_clean_body import get_clean_body


class TestGetCleanBody(unittest.TestCase):

    def test_get_clean_body_14955(self):
        """
        Trying to fix issue 14955
        https://github.com/andresriancho/w3af/issues/14955
        """
        url = URL('http://w3af.org/.git/.git/.git/index')
        headers = Headers([('Content-Type', 'text/html')])

        body = ('<head><title>Document Moved</title></head>'
                '<body><h1>Object Moved</h1>This document may be found '
                '<a HREF="http://w3af.org/.git/.git/.git/index/">here</a></body>')

        resp = HTTPResponse(200, body, headers, url, url)

        clean_body = get_clean_body(resp)

        ebody = ('<head><title>Document Moved</title></head>'
                 '<body><h1>Object Moved</h1>This document may be found '
                 '<a HREF="/">here</a></body>')
        self.assertEqual(clean_body, ebody)

    def test_get_clean_body_14956(self):
        """
        Trying to fix issue 14956
        https://github.com/andresriancho/w3af/issues/14956
        """
        url = URL('http://w3af.org/install.php?mode=phpinfo')
        headers = Headers([('Content-Type', 'text/html')])

        # Note that the redirect changes the protocol, which is probably why the
        # get_clean_body wasn't removing the URL from the body
        #
        # Also, after this URL is not removed
        body = ('<head><title>Document Moved</title></head>'
                '<body><h1>Object Moved</h1>This document may be found '
                '<a HREF="https://w3af.org/install.php?mode=phpinfo">here</a></body>')

        resp = HTTPResponse(200, body, headers, url, url)

        clean_body = get_clean_body(resp)

        ebody = ('<head><title>Document Moved</title></head>'
                 '<body><h1>Object Moved</h1>This document may be found '
                 '<a HREF="">here</a></body>')
        self.assertEqual(clean_body, ebody)
