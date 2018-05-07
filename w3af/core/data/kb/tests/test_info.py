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
import json
import copy
import cPickle
import unittest

from nose.plugins.attrib import attr
from vulndb.db_vuln import Reference, DBVuln

from w3af.core.data.kb.info import Info
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.dc.query_string import QueryString
from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant
from w3af.core.data.dc.generic.nr_kv_container import NonRepeatKeyValueContainer


BLIND_SQLI_REFS = [{"url": "http://capec.mitre.org/data/definitions/7.html",
                    "title": "MITRE - CAPEC"},
                   {"url": "http://projects.webappsec.org/w/page/13246963/SQL%20Injection",
                    "title": "WASC"},
                   {"url": "http://www.w3schools.com/sql/sql_injection.asp",
                    "title": "W3 Schools"},
                   {"url": "https://www.owasp.org/index.php/Blind_SQL_Injection",
                    "title": "OWASP"}]

BLIND_SQLI_TOP10_REFS = [
   {u'link': u'https://www.owasp.org/index.php/Top_10_2013-A1',
    u'owasp_version': u'2013',
    u'risk_id': 1}
]


class MockInfo(Info):
    LONG_DESC = 'Foo bar spam eggs' * 10

    def __init__(self, ids=1, desc=None):
        super(MockInfo, self).__init__('TestCase',
                                       desc or self.LONG_DESC,
                                       ids,
                                       'plugin_name')


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

    def test_get_desc_new_line(self):
        """
        https://github.com/andresriancho/w3af/issues/12220
        """
        i = MockInfo(desc=('This is a rather long and complex desc which has'
                           'a new line at the end.\n\n'))

        self.assertIn('\n\nThis information was', i.get_desc())

    def test_pickleable(self):
        cPickle.dumps(MockInfo())

    def test_data_container_default(self):
        """
        These come from EmptyFuzzableRequest
        """
        info = MockInfo()

        self.assertIsInstance(info.get_dc(), NonRepeatKeyValueContainer)
        self.assertIsNone(info.get_token_name())

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
        self.assertEqual(inst1.get_url(), inst2.get_url())
        self.assertEqual(inst1.get_method(), inst2.get_method())
        self.assertEqual(inst1.get_to_highlight(), inst2.get_to_highlight())

        self.assertEqual(inst2.get_uri(), url)
        self.assertEqual(inst2['eggs'], 'spam')

    def test_from_mutant(self):
        url = URL('http://moth/?a=1&b=2')
        payloads = ['abc', 'def']

        freq = FuzzableRequest(url)
        fuzzer_config = {}
        
        created_mutants = QSMutant.create_mutants(freq, payloads, [], False,
                                                  fuzzer_config)
                
        mutant = created_mutants[0]
        
        inst = Info.from_mutant('TestCase', 'desc' * 30, 1, 'plugin_name',
                                mutant)
        
        self.assertIsInstance(inst, Info)
        
        self.assertEqual(inst.get_uri(), mutant.get_uri())
        self.assertEqual(inst.get_url(), mutant.get_url())
        self.assertEqual(inst.get_method(), mutant.get_method())
        self.assertEqual(inst.get_dc(), mutant.get_dc())
        self.assertIsInstance(inst.get_dc(), QueryString)

    def test_get_uniq_id(self):
        uri = URL('http://www.w3af.com/')

        i = MockInfo()
        i.set_uri(uri)

        self.assertIsInstance(i.get_uniq_id(), str)

    def test_get_uniq_id_with_copy(self):
        uri = URL('http://www.w3af.com/')

        i1 = MockInfo()
        i1.set_uri(uri)

        i2 = copy.deepcopy(i1)

        self.assertEqual(i1.get_uniq_id(), i2.get_uniq_id())

    def test_vulndb_id_not_set(self):
        i = Info('TestCase', MockInfo.LONG_DESC, 1, 'plugin_name')
        self.assertFalse(i.has_db_details())

    def test_vulndb_id_set(self):
        # The vulndb_id overrides the 'Blind SQL injection vulnerability' name
        i = Info('Blind SQL injection vulnerability', MockInfo.LONG_DESC, 1,
                 'plugin_name', vulndb_id=17)

        # lazy calculation
        self.assertIsNone(i._vulndb)

        url = 'https://www.owasp.org/index.php/PHP_File_Inclusion'
        title = 'OWASP'
        expected_references = [Reference(url, title)]

        self.assertTrue(i.has_db_details())
        self.assertEqual(i.get_vulndb_id(), 17)
        self.assertIsInstance(i.get_long_description(), basestring)
        self.assertIsInstance(i.get_fix_guidance(), basestring)
        self.assertEqual(i.get_fix_effort(), 50)
        self.assertEqual(i.get_tags(), ['web', 'file', 'inclusion', 'error',
                                        'injection'])
        self.assertEqual(i.get_wasc_ids(), [])
        self.assertEqual(list(i.get_wasc_urls()), [])
        self.assertEqual(list(i.get_cwe_urls()),
                         ['https://cwe.mitre.org/data/definitions/98.html'])
        self.assertEqual(i.get_cwe_ids(), [u'98'])
        self.assertEqual(i.get_references(), expected_references)
        self.assertEqual(list(i.get_owasp_top_10_references()),
                         [(u'2013', 1,
                           'https://www.owasp.org/index.php/Top_10_2013-A1')])
        self.assertIsInstance(i.get_vuln_info_from_db(), DBVuln)

        # lazy calculation success
        self.assertIsNotNone(i._vulndb)

    def test_vulndb_id_get_from_name(self):
        # Since there is no vulndb_id set, the name wins:
        i = Info('Blind SQL injection vulnerability', MockInfo.LONG_DESC, 1,
                 'plugin_name')

        # lazy calculation
        self.assertIsNone(i._vulndb)

        expected_references = [Reference(d['url'], d['title']) for d in BLIND_SQLI_REFS]

        self.assertTrue(i.has_db_details())
        self.assertEqual(i.get_vulndb_id(), 46)
        self.assertIsInstance(i.get_long_description(), basestring)
        self.assertIsInstance(i.get_fix_guidance(), basestring)
        self.assertEqual(i.get_fix_effort(), 50)
        self.assertEqual(i.get_tags(), [u'web', u'sql', u'blind',
                                        u'injection', u'database'])
        self.assertEqual(i.get_wasc_ids(), [])
        self.assertEqual(list(i.get_wasc_urls()), [])
        self.assertEqual(list(i.get_cwe_urls()),
                         [u'https://cwe.mitre.org/data/definitions/89.html'])
        self.assertEqual(i.get_cwe_ids(), [u'89'])
        self.assertEqual(i.get_references(), expected_references)
        self.assertEqual(list(i.get_owasp_top_10_references()),
                         [(u'2013', 1,
                           'https://www.owasp.org/index.php/Top_10_2013-A1')])
        self.assertIsInstance(i.get_vuln_info_from_db(), DBVuln)

        # lazy calculation success
        self.assertIsNotNone(i._vulndb)

    def test_to_json(self):
        i = Info('Blind SQL injection vulnerability', MockInfo.LONG_DESC, 1,
                 'plugin_name')

        i['test'] = 'foo'
        i.add_to_highlight('abc', 'def')

        jd = i.to_json()
        json_string = json.dumps(jd)
        jd = json.loads(json_string)

        self.assertEqual(jd['name'], i.get_name())
        self.assertEqual(jd['url'], str(i.get_url()))
        self.assertEqual(jd['var'], i.get_token_name())
        self.assertEqual(jd['response_ids'], i.get_id())
        self.assertEqual(jd['vulndb_id'], i.get_vulndb_id())
        self.assertEqual(jd['desc'], i.get_desc(with_id=False))
        self.assertEqual(jd['long_description'], i.get_long_description())
        self.assertEqual(jd['fix_guidance'], i.get_fix_guidance())
        self.assertEqual(jd['fix_effort'], i.get_fix_effort())
        self.assertEqual(jd['tags'], i.get_tags())
        self.assertEqual(jd['wasc_ids'], i.get_wasc_ids())
        self.assertEqual(jd['wasc_urls'], list(i.get_wasc_urls()))
        self.assertEqual(jd['cwe_urls'], list(i.get_cwe_urls()))
        self.assertEqual(jd['references'], BLIND_SQLI_REFS)
        self.assertEqual(jd['owasp_top_10_references'], BLIND_SQLI_TOP10_REFS)
        self.assertEqual(jd['plugin_name'], i.get_plugin_name())
        self.assertEqual(jd['severity'], i.get_severity())
        self.assertEqual(jd['attributes'], i.copy())
        self.assertEqual(jd['highlight'], list(i.get_to_highlight()))

