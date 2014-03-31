"""
test_mangle.py

Copyright 2014 Andres Riancho

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

from nose.plugins.attrib import attr

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.controllers.w3afCore import w3afCore


class TestMangleHandler(unittest.TestCase):

    @attr('moth')
    def test_mangle_handler_raw_request_1326(self):
        """
        Reproduces [0] to make sure we don't make that mistake again.

        [0] https://github.com/andresriancho/w3af/issues/1326
        """
        http_request = 'GET %s HTTP/1.1\n' \
                       'Host: localhost\n' \
                       'Foo: bar\n'
        http_request %= get_moth_http()

        w3af_core = w3afCore()
        w3af_core.plugins.set_plugins(['sed'], 'mangle')
        w3af_core.plugins.init_plugins()

        resp = w3af_core.uri_opener.send_raw_request(http_request, None)
        self.assertEqual(resp.get_code(), 200)
