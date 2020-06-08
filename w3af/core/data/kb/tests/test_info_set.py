# -*- coding: utf-8 -*-
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
import copy
import json
import unittest

from nose.plugins.attrib import attr
from cPickle import loads

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.kb.info import Info
from w3af.core.data.kb.info_set import InfoSet
from w3af.core.data.misc.cpickle_dumps import cpickle_dumps
from w3af.core.data.kb.tests.test_info import (MockInfo, BLIND_SQLI_REFS,
                                               BLIND_SQLI_TOP10_REFS)


@attr('smoke')
class TestInfoSet(unittest.TestCase):
    def test_not_empty(self):
        self.assertRaises(ValueError, InfoSet, [])

    def test_get_name(self):
        i = MockInfo()
        iset = InfoSet([i])
        self.assertEqual(iset.get_name(), 'TestCase')

    def test_get_desc_no_template(self):
        i = MockInfo()
        iset = InfoSet([i])
        self.assertEqual(iset.get_desc(), MockInfo.LONG_DESC)

    def test_get_desc_template(self):
        i = MockInfo()
        tiset = TemplatedInfoSet([i])
        self.assertEqual(tiset.get_desc(), 'Foos and bars 1')

    def test_get_desc_template_info_attr_access(self):
        value = 'Yuuup!'

        i = MockInfo()
        i['tag'] = value
        iset = InfoSet([i])
        iset.TEMPLATE = '{{ tag }}'

        self.assertEqual(iset.get_desc(), value)

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
        added = iset.add(i2)

        self.assertEqual(iset.get_id(), [1, 2])
        self.assertTrue(added)

    def test_add_more_than_max(self):
        i1 = MockInfo(ids=1)
        i2 = MockInfo(ids=2)

        iset = InfoSet([i1])
        iset.MAX_INFO_INSTANCES = 2

        added = iset.add(i1)
        self.assertTrue(added)

        added = iset.add(i2)
        self.assertFalse(added)

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

    def test_deepcopy(self):
        i = MockInfo()
        iset1 = InfoSet([i])

        iset1_copy = copy.deepcopy(iset1)

        self.assertEqual(iset1.get_uniq_id(), iset1_copy.get_uniq_id())

    def test_to_json(self):
        i = Info('Blind SQL injection vulnerability',
                 MockInfo.LONG_DESC,
                 1,
                 'plugin_name')

        i['test'] = 'foo'
        i.add_to_highlight('abc', 'def')

        iset = InfoSet([i])

        jd = iset.to_json()
        json_string = json.dumps(jd)
        jd = json.loads(json_string)

        self.assertEqual(jd['name'], iset.get_name())
        self.assertEqual(jd['url'], str(iset.get_url()))
        self.assertEqual(jd['var'], iset.get_token_name())
        self.assertEqual(jd['response_ids'], iset.get_id())
        self.assertEqual(jd['vulndb_id'], iset.get_vulndb_id())
        self.assertEqual(jd['desc'], iset.get_desc(with_id=False))
        self.assertEqual(jd['long_description'], iset.get_long_description())
        self.assertEqual(jd['fix_guidance'], iset.get_fix_guidance())
        self.assertEqual(jd['fix_effort'], iset.get_fix_effort())
        self.assertEqual(jd['tags'], iset.get_tags())
        self.assertEqual(jd['wasc_ids'], iset.get_wasc_ids())
        self.assertEqual(jd['wasc_urls'], list(iset.get_wasc_urls()))
        self.assertEqual(jd['cwe_urls'], list(iset.get_cwe_urls()))
        self.assertEqual(jd['references'], BLIND_SQLI_REFS)
        self.assertEqual(jd['owasp_top_10_references'], BLIND_SQLI_TOP10_REFS)
        self.assertEqual(jd['plugin_name'], iset.get_plugin_name())
        self.assertEqual(jd['severity'], iset.get_severity())
        self.assertEqual(jd['attributes'], iset.first_info.copy())
        self.assertEqual(jd['highlight'], list(iset.get_to_highlight()))

    def test_match_different_itag(self):
        """
        https://github.com/andresriancho/w3af/issues/10286
        """
        itag_1 = 'hello'
        i1 = MockInfo(ids=1)
        i1[itag_1] = 1
        iset_1 = InfoSet([i1])
        iset_1.ITAG = itag_1

        itag_2 = 'world'
        i2 = MockInfo(ids=2)
        i2[itag_2] = 2

        self.assertFalse(iset_1.match(i2))

    def test_match_same_itag(self):
        """
        https://github.com/andresriancho/w3af/issues/10286
        """
        itag_1 = 'hello'
        i1 = MockInfo(ids=1)
        i1[itag_1] = 1
        iset_1 = InfoSet([i1])
        iset_1.ITAG = itag_1

        i2 = MockInfo(ids=2)
        i2[itag_1] = 1

        self.assertTrue(iset_1.match(i2))

    def test_get_desc_urls(self):
        i1 = MockInfo()
        i1.set_url(URL('http://w3af.org/1'))

        i2 = MockInfo()
        i2.set_url(URL('http://w3af.org/2'))

        tiset = TemplatedInfoSetPrintUri([i1, i2])
        expected = u' - http://w3af.org/2\n - http://w3af.org/1\n'
        self.assertEqual(tiset.get_desc(), expected)

    def test_get_desc_template_special_chars_unicode(self):
        i1 = MockInfo()
        i1.set_url(URL('http://w3af.org/1'))

        i2 = MockInfo()
        i2.set_url(URL('http://w3af.org/2\xc3\xb6'))

        tiset = TemplatedInfoSetPrintUri([i1, i2])
        expected = u' - http://w3af.org/1\n - http://w3af.org/2ö\n'
        self.assertEqual(tiset.get_desc(), expected)


class TemplatedInfoSet(InfoSet):
    TEMPLATE = '''\
    Foos and bars {{ uris|length }}
    '''


class TemplatedInfoSetPrintUri(InfoSet):
    TEMPLATE = (
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )