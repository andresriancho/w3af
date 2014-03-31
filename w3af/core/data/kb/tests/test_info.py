"""
test_info.py

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
import cPickle

from nose.plugins.attrib import attr

from w3af.core.data.kb.info import Info
from w3af.core.data.parsers.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.dc.data_container import DataContainer
from w3af.core.data.fuzzer.mutants.mutant import Mutant


class MockInfo(Info):
    def __init__(self):
        long_desc = 'Foo bar spam eggs' * 10
        super(MockInfo, self).__init__('TestCase', long_desc, 1, 'plugin_name')

@attr('smoke')
class TestInfo(unittest.TestCase):
    """
    Simplest tests for info. Mainly started because of incompatibilities between
    nosetests, doctest and "_".

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def test_convert_to_range(self):
        inf = MockInfo()

        res = inf._convert_to_range_wrapper([1, 2, 3, 4, 5, 6])
        self.assertEquals('1 to 6', res)

        res = inf._convert_to_range_wrapper([1, 2, 3, 6])
        self.assertEquals('1 to 3 and 6', res)

        res = inf._convert_to_range_wrapper([1, 2, 3, 6, 7, 8])
        self.assertEquals('1 to 3, 6 to 8', res)

        res = inf._convert_to_range_wrapper([1, 2, 3, 6, 7, 8, 10])
        self.assertEquals('1 to 3, 6 to 8 and 10', res)

        res = inf._convert_to_range_wrapper([1, 2, 3, 10, 20, 30])
        self.assertEquals('1 to 3, 10, 20 and 30', res)

        res = inf._convert_to_range_wrapper([1, 3, 10, 20, 30])
        self.assertEquals('1, 3, 10, 20 and 30', res)

        res = len(inf._convert_to_range_wrapper(range(0, 30000, 2)).split())
        self.assertEquals(15001, res)

    def test_set_uri(self):
        i = MockInfo()
        self.assertRaises(TypeError, i.set_uri, 'http://www.w3af.com/')
        
        uri = URL('http://www.w3af.com/')
        i.set_uri(uri)
        self.assertEqual(i.get_uri(), uri)

    def test_set_url(self):
        i = MockInfo()
        self.assertRaises(TypeError, i.set_url, 'http://www.w3af.com/?id=1')
        
        uri = URL('http://www.w3af.com/?id=1')
        url = URL('http://www.w3af.com/')
        
        i.set_url(uri)
        
        self.assertEqual(i.get_uri(), uri)
        self.assertEqual(i.get_url(), url)
    
    def test_set_desc(self):
        i = MockInfo()
        
        self.assertRaises(ValueError, i.set_desc, 'abc')
        
        desc = 'abc ' * 30
        i.set_desc(desc)
        self.assertTrue(i.get_desc().startswith(desc))
    
    def test_pickleable(self):
        cPickle.dumps(MockInfo())
    
    def test_from_info(self):
        url = URL('http://moth/')
        
        inst1 = MockInfo()
        inst1.set_uri(url)
        inst1['eggs'] = 'spam'
        
        inst2 = Info.from_info(inst1)
        
        self.assertNotEqual(id(inst1), id(inst2))
        self.assertIsInstance(inst2, Info)
        
        self.assertEqual(inst1.get_uri(), inst2.get_uri())
        self.assertEqual(inst1.get_uri(), url)
        self.assertEqual(inst2.get_uri(), url)
        self.assertEqual(inst2['eggs'], 'spam')
        self.assertEqual(inst1.get_url(), inst2.get_url())
        self.assertEqual(inst1.get_method(), inst2.get_method())
        self.assertEqual(inst1.get_dc(), inst2.get_dc())
        self.assertEqual(inst1.get_var(), inst2.get_var())
        self.assertEqual(inst1.get_to_highlight(), inst2.get_to_highlight())

    def test_from_mutant(self):
        dc = DataContainer()
        url = URL('http://moth/')
        payloads = ['abc', 'def']

        dc['a'] = ['1', ]
        dc['b'] = ['2', ]
        freq = FuzzableRequest(url, dc=dc)
        fuzzer_config = {}
        
        created_mutants = Mutant.create_mutants(freq, payloads, [], False,
                                                fuzzer_config)
                
        mutant = created_mutants[0]
        
        inst = Info.from_mutant('TestCase', 'desc' * 30, 1, 'plugin_name', mutant)
        
        self.assertIsInstance(inst, Info)
        
        self.assertEqual(inst.get_uri(), mutant.get_uri())
        self.assertEqual(inst.get_url(), mutant.get_url())
        self.assertEqual(inst.get_method(), mutant.get_method())
        self.assertEqual(inst.get_dc(), mutant.get_dc())
        self.assertEqual(inst.get_var(), mutant.get_var())
    