# -*- encoding: utf-8 -*-
"""
test_multire.py

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
import re
import unittest

from mock import Mock

from w3af.core.controllers.tests.pylint_plugins.decorator import only_if_subclass
from w3af.core.data.esmre.re_multire import re_multire
from w3af.core.data.esmre.esmre_multire import esmre_multire


class BaseMultiReTest(unittest.TestCase):

    klass = Mock()

    @only_if_subclass
    def test_simplest(self):
        re_list = ['123', '456', '789']
        mre = self.klass(re_list)

        result = mre.query('456')
        self.assertEqual(1, len(result))
        self.assertEqual('456', result[0][1])

        result = mre.query('789')
        self.assertEqual(1, len(result))
        self.assertEqual('789', result[0][1])

    @only_if_subclass
    def test_re(self):
        re_list = ['123.*456', 'abc.*def']
        mre = self.klass(re_list)
        result = mre.query('456')
        self.assertEqual(0, len(result))
        self.assertEqual([], result)

        result = mre.query('123a456')
        self.assertEqual(1, len(result))
        self.assertEqual('123.*456', result[0][1])

        result = mre.query('abcAAAdef')
        self.assertEqual(1, len(result))
        self.assertEqual('abc.*def', result[0][1])

    @only_if_subclass
    def test_re_with_obj(self):
        re_list = [('123.*456', None, None), ('abc.*def', 1, 2)]
        mre = self.klass(re_list)

        result = mre.query('123A456')
        self.assertEqual(1, len(result))
        self.assertEqual('123.*456', result[0][1])
        self.assertEqual(None, result[0][3])
        self.assertEqual(None, result[0][4])

        result = mre.query('abcAAAdef')
        self.assertEqual(1, len(result))
        self.assertEqual('abc.*def', result[0][1])
        self.assertEqual(1, result[0][3])
        self.assertEqual(2, result[0][4])

    @only_if_subclass
    def test_re_flags(self):
        re_list = ['123.*456', 'abc.*def']
        mre = self.klass(re_list, re.IGNORECASE)

        result = mre.query('ABC3def')
        self.assertEqual(1, len(result))
        self.assertEqual('abc.*def', result[0][1])

    @only_if_subclass
    def test_unicode_re(self):
        re_list = [u'ñ', u'ý']
        mre = self.klass(re_list)

        result = mre.query('abcn')
        self.assertEqual(0, len(result))
        self.assertEqual([], result)

        result = mre.query('abcñ')
        self.assertEqual(1, len(result))
        self.assertEqual('ñ', result[0][1])

    @only_if_subclass
    def test_unicode_query(self):
        re_list = [u'abc', u'def']
        mre = self.klass(re_list)

        result = mre.query('abcñ')
        self.assertEqual(1, len(result))
        self.assertEqual('abc', result[0][1])

        result = mre.query('abc\\x00def')
        self.assertEqual(2, len(result))
        self.assertEqual('abc', result[0][1])
        self.assertEqual('def', result[1][1])

    @only_if_subclass
    def test_special_char(self):
        re_list = [u'\x00']
        mre = self.klass(re_list)

        result = mre.query('abc\x00def')
        self.assertEqual(1, len(result))
        self.assertEqual('\x00', result[0][1])


class TestEsmreMultire(BaseMultiReTest):
    def __init__(self, testname):
        super(TestEsmreMultire, self).__init__(testname)
        self.klass = esmre_multire


class TestReMultire(BaseMultiReTest):
    def __init__(self, testname):
        super(TestReMultire, self).__init__(testname)
        self.klass = re_multire
