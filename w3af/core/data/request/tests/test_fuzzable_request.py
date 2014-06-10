# -*- coding: utf-8 -*-
"""
test_fuzzablerequest.py

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

from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.generic.kv_container import KeyValueContainer
from w3af.core.data.misc.encoding import smart_unicode
from w3af.core.data.dc.form import Form


@attr('smoke')
class TestFuzzableRequest(unittest.TestCase):

    def setUp(self):
        self.url = URL('http://w3af.com/a/b/c.php')

    def test_dump_case01(self):
        expected = u'\r\n'.join([u'GET http://w3af.com/a/b/c.php HTTP/1.1',
                                 u'Hello: World',
                                 u'',
                                 u'a=b'])

        headers = Headers([(u'Hello', u'World')])
        post_data = KeyValueContainer(init_val=[('a', ['b'])])
        fr = FuzzableRequest(self.url, method='GET', post_data=post_data,
                             headers=headers)

        self.assertEqual(fr.dump(), expected)

    def test_dump_case02(self):
        expected = u'\r\n'.join([u'GET http://w3af.com/a/b/c.php HTTP/1.1',
                                 u'Hola: Múndo',
                                 u'',
                                 u'a=b'])

        headers = Headers([(u'Hola', u'Múndo')])
        post_data = KeyValueContainer(init_val=[('a', ['b'])])
        fr = FuzzableRequest(self.url, method='GET', post_data=post_data,
                             headers=headers)

        self.assertEqual(fr.dump(), expected.encode('utf-8'))

    def test_dump_case03(self):
        header_value = ''.join(chr(i) for i in xrange(256))
        
        expected = u'\r\n'.join([u'GET http://w3af.com/a/b/c.php HTTP/1.1',
                                 u'Hola: %s' % smart_unicode(header_value),
                                 u'',
                                 u'a=b'])

        headers = Headers([(u'Hola', header_value)])
        post_data = KeyValueContainer(init_val=[('a', ['b'])])
        fr = FuzzableRequest(self.url, method='GET', post_data=post_data,
                             headers=headers)

        self.assertEqual(fr.dump(), expected)

    def test_dump_mangle(self):
        fr = FuzzableRequest(URL("http://www.w3af.com/"),\
                             headers=Headers([('Host', 'www.w3af.com')]))

        expected = u'\r\n'.join([u'GET http://www.w3af.com/ HTTP/1.1',
                                 u'Host: www.w3af.com',
                                 u'',
                                 u''])
        
        self.assertEqual(fr.dump(), expected)
        
        fr.set_method('POST')
        fr.set_data(KeyValueContainer(init_val=[('data', ['23'])]))
        
        expected = u'\r\n'.join([u'POST http://www.w3af.com/ HTTP/1.1',
                                 u'Host: www.w3af.com',
                                 u'',
                                 u'data=23'])
        
        self.assertEqual(fr.dump(), expected)

    def test_export_without_post_data(self):
        fr = FuzzableRequest(URL("http://www.w3af.com/"))
        self.assertEqual(fr.export(), '"GET","http://www.w3af.com/",""')
    
    def test_export_with_post_data(self):
        dc = KeyValueContainer(init_val=[('a', ['1'])])
        fr = FuzzableRequest(URL("http://www.w3af.com/"), post_data=dc)

        self.assertEqual(fr.export(), '"GET","http://www.w3af.com/","a=1"')
        
    def test_equal(self):
        u = URL("""http://www.w3af.com/""")
        fr1 = FuzzableRequest(u)
        fr2 = FuzzableRequest(u)
        self.assertEqual(fr1, fr2)

        fr1 = FuzzableRequest(URL("http://www.w3af.com/a"))
        fr2 = FuzzableRequest(URL("http://www.w3af.com/b"))
        self.assertNotEqual(fr1, fr2)
        
        fr1 = FuzzableRequest(u)
        fr2 = FuzzableRequest(u, method='POST')
        self.assertNotEqual(fr1, fr2)
    
    def test_set_url(self):
        self.assertRaises(TypeError, FuzzableRequest, 'http://www.google.com/')
        
        url = URL('http://www.google.com/')
        r = FuzzableRequest(url)
        self.assertEqual(r.get_url(), url)

    def test_str_no_qs(self):
        fr = FuzzableRequest(URL("http://www.w3af.com/"))
        expected = 'http://www.w3af.com/ | Method: GET | Query string parameters: ()'
        self.assertEqual(str(fr), expected)

    def test_str_qs(self):
        fr = FuzzableRequest(URL("http://www.w3af.com/?id=3"))
        expected = 'http://www.w3af.com/ | Method: GET | Query string parameters: (id)'
        self.assertEqual(str(fr), expected)

    def test_str_with_postdata(self):
        fr = FuzzableRequest.from_parts("http://www.w3af.com/", post_data='a=1')
        expected = 'http://www.w3af.com/ | Method: GET | Form parameters: (a)'
        self.assertEqual(str(fr), expected)

    def test_str_with_qs_and_postdata(self):
        fr = FuzzableRequest.from_parts("http://www.w3af.com/?id=3",
                                        post_data='a=1&b=3&a=2')
        expected = 'http://www.w3af.com/ | Method: GET | Form parameters: (a,a,b)'
        self.assertEqual(str(fr), expected)

    def test_repr(self):
        url = "http://www.w3af.com/"
        fr = FuzzableRequest(URL(url))

        self.assertEqual(repr(fr), '<fuzzable request | GET | %s>' % url)

    def test_sent_url(self):
        f = FuzzableRequest(URL('''http://example.com/a?p=d'z"0&paged=2'''))
        self.assertTrue(f.sent('d%5C%27z%5C%220'))

        f = FuzzableRequest(URL('http://example.com/a?p=<SCrIPT>alert("bsMs")</SCrIPT>'))
        self.assertTrue(f.sent('<SCrIPT>alert(\"bsMs\")</SCrIPT>'))

        f = FuzzableRequest(URL('http://example.com/?p=<ScRIPT>a=/PlaO/%0Afake_alert(a.source)</SCRiPT>'))
        self.assertTrue(f.sent('<ScRIPT>a=/PlaO/fake_alert(a.source)</SCRiPT>'))

    def test_sent_post_data(self):
        form = Form()
        form.add_input([("name", "username"), ("value", """d'z"0""")])
        form.add_input([("name", "address"), ("value", "")])

        f = FuzzableRequest(URL('http://example.com/'), post_data=form)
        self.assertTrue(f.sent('d%5C%27z%5C%220'))
