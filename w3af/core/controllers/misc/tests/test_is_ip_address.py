"""
test_is_ip_address.py

Copyright 2010 Andres Riancho

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

from w3af.core.controllers.misc.is_ip_address import is_ip_address, is_ipv6_address


class TestIsIPAddress4(unittest.TestCase):
    
    def test_is_ip_address_true(self):
        self.assertTrue(is_ip_address('127.0.0.1'))
    
    def test_is_ip_address_false_case01(self):
        self.assertFalse(is_ip_address('127.0.0.1.2'))
    
    def test_is_ip_address_false_case02(self):
        self.assertFalse(is_ip_address('127.0.0.256'))


class TestIsIPAddress6(unittest.TestCase):
    def test_is_ip_address_6_true_01(self):
        self.assertTrue(is_ipv6_address('2001:0db8:85a3:0000:0000:8a2e:0370:7334'))

    def test_is_ip_address_6_true_02(self):
        self.assertTrue(is_ipv6_address('2001:db8:85a3:0:0:8a2e:370:7334'))

    def test_is_ip_address_6_true_03(self):
        self.assertTrue(is_ipv6_address('2001:db8:85a3::8a2e:370:7334'))

    def test_is_ip_address_6_true_04(self):
        self.assertTrue(is_ipv6_address('::1'))

    def test_is_ip_address_6_false_01(self):
        self.assertFalse(is_ipv6_address(':'))

    def test_is_ip_address_6_false_02(self):
        self.assertFalse(is_ipv6_address('x::1'))

    def test_is_ip_address_6_false_03(self):
        self.assertFalse(is_ipv6_address('x::'))
