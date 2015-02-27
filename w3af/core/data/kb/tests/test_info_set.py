"""
test_info_set.py

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

from nose.plugins.attrib import attr
from cPickle import loads

from w3af.core.data.kb.tests.test_info import MockInfo
from w3af.core.data.kb.info_set import InfoSet
from w3af.core.data.misc.cpickle_dumps import cpickle_dumps


@attr('smoke')
class TestInfoSet(unittest.TestCase):
    def test_not_empty(self):
        self.assertRaises(ValueError, InfoSet, [])

    def test_get_name(self):
        i = MockInfo()
        iset = InfoSet([i])
        self.assertEqual(iset.get_name(), 'TestCase')

    def test_get_desc(self):
        i = MockInfo()
        iset = InfoSet([i])
        self.assertEqual(iset.get_desc(), MockInfo.LONG_DESC)

    def test_get_id(self):
        i1 = MockInfo(ids=1)
        i2 = MockInfo(ids=2)
        iset = InfoSet([i2, i1])
        self.assertEqual(iset.get_id(), [1, 2])

    def test_get_plugin_name(self):
        i = MockInfo()
        iset = InfoSet([i])
        self.assertEqual(iset.get_plugin_name(), 'plugin_name')

    def test_add(self):
        i1 = MockInfo(ids=1)
        i2 = MockInfo(ids=2)
        iset = InfoSet([i1])
        iset.add(i2)
        self.assertEqual(iset.get_id(), [1, 2])

    def test_get_uniq_id(self):
        i = MockInfo()
        iset = InfoSet([i])
        self.assertIsNotNone(iset.get_uniq_id())

    def test_eq(self):
        i = MockInfo()
        iset1 = InfoSet([i])

        i = MockInfo()
        iset2 = InfoSet([i])

        self.assertEqual(iset1, iset2)

    def test_pickle(self):
        i = MockInfo()
        iset1 = InfoSet([i])

        pickled_iset1 = cpickle_dumps(iset1)
        iset1_clone = loads(pickled_iset1)

        self.assertEqual(iset1.get_uniq_id(), iset1_clone.get_uniq_id())
