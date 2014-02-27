"""
test_form_filler.py

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

from nose.plugins.attrib import attr

from w3af.core.data.fuzzer.form_filler import smart_fill


@attr('smoke')
class TestSmartFill(unittest.TestCase):

    def test_address(self):
        self.assertEquals(smart_fill('address'), 'Bonsai Street 123')

    def test_address_2(self):
        self.assertEquals(smart_fill('street_address'), 'Bonsai Street 123')

    def test_ip(self):
        self.assertEquals(smart_fill('ip'), '127.0.0.1')

    def test_ip_case_insensitive(self):
        self.assertEquals(smart_fill('IP'), '127.0.0.1')

    def test_default(self):
        self.assertEquals(smart_fill('foobar'), '56')
