"""
test_response.py

Copyright 2018 Andres Riancho

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

from w3af.core.controllers.core_helpers.not_found.response import FourOhFourResponse
from w3af.core.data.parsers.doc.url import URL

from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers


class TestFourOhFourResponse(unittest.TestCase):
    def test_normalize_path_paths(self):
        url = URL('https://w3af.org/a/b/c/')
        normalized_path = FourOhFourResponse.normalize_path(url)

        self.assertEqual(normalized_path, 'https://w3af.org/a/b/path/')

    def test_normalize_path_filenames(self):
        url_0 = URL('https://w3af.org/assets/uploads/2015/09/index.php')
        normalized_path_0 = FourOhFourResponse.normalize_path(url_0)

        url_1 = URL('https://w3af.org/assets/uploads/2015/09/nidex.php')
        normalized_path_1 = FourOhFourResponse.normalize_path(url_1)

        url_2 = URL('https://w3af.org/assets/uploads/2015/09/hppvresion.php')
        normalized_path_2 = FourOhFourResponse.normalize_path(url_2)

        self.assertEqual(normalized_path_0, normalized_path_1)
        self.assertEqual(normalized_path_1, normalized_path_2)

    def test_normalize_path_with_querystring(self):
        url_0 = URL('https://w3af.org/index.php?id=1')
        normalized_path_0 = FourOhFourResponse.normalize_path(url_0)

        url_1 = URL('https://w3af.org/test.php?id=3')
        normalized_path_1 = FourOhFourResponse.normalize_path(url_1)

        self.assertEqual(normalized_path_0, normalized_path_1)

    def test_normalize_path_with_querystring_no_filename(self):
        url_0 = URL('https://w3af.org/?id=1')
        normalized_path_0 = FourOhFourResponse.normalize_path(url_0)

        url_1 = URL('https://w3af.org/?id=3')
        normalized_path_1 = FourOhFourResponse.normalize_path(url_1)

        self.assertEqual(normalized_path_0, normalized_path_1)

    def test_dict_transformations(self):
        url = URL('http://w3af.com')
        headers = Headers([('Content-Type', 'text/html')])
        body = ''

        http_response = HTTPResponse(200, body, headers, url, url)

        clean_response = FourOhFourResponse.from_http_response(http_response)
        clean_response.diff = ''
        clean_response.diff_with_id = 1

        clean_response_dict = clean_response.to_dict()
        clean_response_from_dict = FourOhFourResponse.from_dict(clean_response_dict)

        self.assertEqual(clean_response, clean_response_from_dict)

    def test_msgpack_transformations(self):
        url = URL('http://w3af.com')
        headers = Headers([('Content-Type', 'text/html')])
        body = ''

        http_response = HTTPResponse(200, body, headers, url, url)

        clean_response = FourOhFourResponse.from_http_response(http_response)
        clean_response.diff = ''
        clean_response.diff_with_id = 1

        clean_response_serialized = clean_response.dumps()
        clean_response_from_msgpack = FourOhFourResponse.loads(clean_response_serialized)

        self.assertEqual(clean_response, clean_response_from_msgpack)
