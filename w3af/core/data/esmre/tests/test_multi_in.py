# -*- encoding: utf-8 -*-
"""
test_multiin.py

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

from mock import Mock

from w3af.core.controllers.tests.pylint_plugins.decorator import only_if_subclass
from w3af.core.data.esmre.in_multi_in import in_multi_in
from w3af.core.data.esmre.esm_multi_in import esm_multi_in


class BaseMultiInTest(unittest.TestCase):

    klass = Mock()

    @only_if_subclass
    def test_simplest(self):
        in_list = ['123', '456', '789']
        imi = self.klass(in_list)

        result = imi.query('456')
        self.assertEqual(1, len(result))
        self.assertEqual('456', result[0])

        result = imi.query('789')
        self.assertEqual(1, len(result))
        self.assertEqual('789', result[0])

    @only_if_subclass
    def test_assoc_obj(self):
        in_list = [('123456', None, None), ('abcdef', 1, 2)]
        imi = self.klass(in_list)

        result = imi.query('spam1234567890eggs')
        self.assertEqual(1, len(result))
        self.assertEqual('123456', result[0][0])
        self.assertEqual(None, result[0][1])
        self.assertEqual(None, result[0][2])

        result = imi.query('foo abcdef bar')
        self.assertEqual(1, len(result))
        self.assertEqual('abcdef', result[0][0])
        self.assertEqual(1, result[0][1])
        self.assertEqual(2, result[0][2])

    @only_if_subclass
    def test_special_char(self):
        in_list = ['javax.naming.NameNotFoundException', '7', '8']
        imi = self.klass(in_list)

        result = imi.query(
            'abc \\n javax.naming.NameNotFoundException \\n 123')
        self.assertEqual(1, len(result))
        self.assertEqual('javax.naming.NameNotFoundException', result[0])

        in_list = [u'abc(def)', u'foo(bar)']
        imi = self.klass(in_list)

        result = imi.query('foo abc(def) bar')
        self.assertEqual(1, len(result))
        self.assertEqual('abc(def)', result[0])

    @only_if_subclass
    def test_unicode(self):
        in_list = [u'ñ', u'ý']
        imi = self.klass(in_list)

        result = imi.query('abcn')
        self.assertEqual(0, len(result))

        result = imi.query('abcñ')
        self.assertEqual(1, len(result))
        self.assertEqual('ñ', result[0])

    @only_if_subclass
    def test_null_byte(self):
        in_list = ['\x00']
        imi = self.klass(in_list)

        result = imi.query('abc\x00def')
        self.assertEqual(1, len(result))
        self.assertEqual('\x00', result[0])


class TestEsmMultiIn(BaseMultiInTest):
    def __init__(self, testname):
        super(TestEsmMultiIn, self).__init__(testname)
        self.klass = esm_multi_in


class TestInMultiIn(BaseMultiInTest):
    def __init__(self, testname):
        super(TestInMultiIn, self).__init__(testname)
        self.klass = in_multi_in
