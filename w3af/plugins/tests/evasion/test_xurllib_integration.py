"""
test_xurllib_integration.py

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
from unittest.case import skip

from nose.plugins.attrib import attr

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.plugins.evasion.self_reference import self_reference


@attr('moth')
@skip('URL normalization breaks evasion. @see: 4fa67fbb')
class TestXurllibIntegration(unittest.TestCase):
    
    def test_send_mangled(self):
        xurllib = ExtendedUrllib()
        
        xurllib.set_evasion_plugins([self_reference(), ])
        url = URL('http://moth/')
        
        http_response = xurllib.GET(url)
        self.assertEqual(http_response.get_url().url_string,
                         u'http://moth/./')