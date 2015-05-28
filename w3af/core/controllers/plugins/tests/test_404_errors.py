"""
test_404_errors.py

Copyright 2015 Andres Riancho

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

from mock import patch, call

import w3af.core.data.kb.knowledge_base as kb
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.core.controllers.exceptions import FourOhFourDetectionException
from w3af.plugins.grep.meta_tags import meta_tags


class Test404Errors(unittest.TestCase):
    def setUp(self):
        create_temp_dir()
        kb.kb.cleanup()
        self.plugin = meta_tags()

    def tearDown(self):
        kb.kb.cleanup()

    def test_handles_404_exception(self):
        body = '<meta test="user/pass"></script>'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=1)

        with patch('w3af.plugins.grep.meta_tags.is_404') as is_404_mock,\
        patch('w3af.core.controllers.plugins.grep_plugin.om.out') as om_mock:
            msg = 'Exception found while detecting 404: "UnitTest"'
            is_404_mock.side_effect = FourOhFourDetectionException(msg)

            self.plugin.grep_wrapper(request, resp)

            ecall = call.debug(msg)
            vulns = kb.kb.get('meta_tags', 'meta_tags')

            self.assertIn(ecall, om_mock.mock_calls)
            self.assertEqual(vulns, [])

    def test_raises_other_exceptions(self):
        body = '<meta test="user/pass"></script>'
        url = URL('http://www.w3af.com/')
        headers = Headers([('content-type', 'text/html')])
        request = FuzzableRequest(url, method='GET')
        resp = HTTPResponse(200, body, headers, url, url, _id=1)

        with patch('w3af.plugins.grep.meta_tags.is_404') as is_404_mock:
            msg = 'Foos and bars'
            is_404_mock.side_effect = Exception(msg)

            try:
                self.plugin.grep_wrapper(request, resp)
            except Exception, e:
                self.assertEqual(str(e), msg)
            else:
                self.assertTrue(False, 'Expected exception, success found!')