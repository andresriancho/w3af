"""
test_vuln.py

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

from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant
from w3af.core.data.dc.generic.nr_kv_container import NonRepeatKeyValueContainer


class MockVuln(Vuln):
    def __init__(self, name='TestCase', long_desc=None, severity='High',
                 _id=1, plugin_name='plugin_name'):
        
        if long_desc is None:
            long_desc = 'Foo bar spam eggs' * 10
            
        super(MockVuln, self).__init__(name, long_desc, severity,
                                       _id, plugin_name)


@attr('smoke')
class TestVuln(unittest.TestCase):
    
    def test_from_vuln(self):
        url = URL('http://moth/')
        
        inst1 = MockVuln()
        inst1.set_uri(url)
        inst1['eggs'] = 'spam'
        
        inst2 = Vuln.from_vuln(inst1)
        
        self.assertNotEqual(id(inst1), id(inst2))
        self.assertIsInstance(inst2, Vuln)
        
        self.assertEqual(inst1.get_uri(), inst2.get_uri())
        self.assertEqual(inst1.get_uri(), url)
        self.assertEqual(inst2.get_uri(), url)
        self.assertEqual(inst2['eggs'], 'spam')
        self.assertEqual(inst1.get_url(), inst2.get_url())
        self.assertEqual(inst1.get_method(), inst2.get_method())
        self.assertEqual(inst1.get_to_highlight(), inst2.get_to_highlight())

        # Since inst1 was created using a EmptyFuzzableRequest, this is fine:
        self.assertIsInstance(inst1.get_dc(), NonRepeatKeyValueContainer)
        self.assertIsNone(inst1.get_token_name())

    def test_from_mutant(self):
        url = URL('http://moth/?a=1&b=2')
        payloads = ['abc', 'def']

        freq = FuzzableRequest(url)
        fuzzer_config = {}
        
        created_mutants = QSMutant.create_mutants(freq, payloads, [], False,
                                                  fuzzer_config)
                
        mutant = created_mutants[0]
        
        inst = Vuln.from_mutant('TestCase', 'desc' * 30, 'High', 1,
                                'plugin_name', mutant)
        
        self.assertIsInstance(inst, Vuln)
        
        self.assertEqual(inst.get_uri(), mutant.get_uri())
        self.assertEqual(inst.get_url(), mutant.get_url())
        self.assertEqual(inst.get_method(), mutant.get_method())
        self.assertEqual(inst.get_dc(), mutant.get_dc())
        self.assertEqual(inst.get_token_name(), mutant.get_token().get_name())
