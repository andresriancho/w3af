# -*- coding: UTF-8 -*-
"""
test_html.py

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

from w3af.core.data.parsers.utils.form_params import FormParameters
from w3af.core.data.parsers.doc.html import HTMLParser
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.doc.tests.test_sgml import build_http_response
from w3af.core.data.parsers.doc.tests.data.constants import *


class RaiseHTMLParser(HTMLParser):
    def _handle_exception(self, where, ex):
        raise ex


@attr('smoke')
class TestHTMLParser(unittest.TestCase):
    
    url = URL('http://w3af.com')

    def test_forms(self):
        body = HTML_DOC % \
            {'head': '',
             'body': FORM_METHOD_GET % {'form_content': ''} +
                     FORM_WITHOUT_ACTION % {'form_content': ''}
             }
        resp = build_http_response(self.url, body)
        p = RaiseHTMLParser(resp)
        p.parse()
        self.assertEquals(2, len(p.forms))

    def test_no_forms(self):
        # No form should be parsed
        body = HTML_DOC % \
            {'head': '',
             'body': (INPUT_TEXT_WITH_NAME + INPUT_HIDDEN + SELECT_WITH_ID +
                      TEXTAREA_WITH_ID_AND_DATA + INPUT_FILE_WITH_NAME)
             }
        resp = build_http_response(self.url, body)
        p = RaiseHTMLParser(resp)
        p.parse()
        self.assertEquals(0, len(p.forms))

    def test_form_without_method(self):
        """
        When the form has no 'method' => 'GET' will be used
        """
        body = HTML_DOC % \
            {'head': '',
                     'body': FORM_WITHOUT_METHOD % {'form_content': ''}
             }
        resp = build_http_response(self.url, body)
        p = RaiseHTMLParser(resp)
        p.parse()
        self.assertEquals('GET', p.forms[0].get_method())

    def test_form_without_action(self):
        """
        If the form has no 'content' => HTTPResponse's url will be used
        """
        body = HTML_DOC % \
            {'head': '',
                     'body': FORM_WITHOUT_ACTION % {'form_content': ''}
             }
        resp = build_http_response(self.url, body)
        p = RaiseHTMLParser(resp)
        p.parse()
        self.assertEquals(self.url, p.forms[0].get_action())

    def test_form_with_invalid_url_in_action(self):
        """
        If an invalid URL is detected in the form's action then use base_url
        """
        body = """
        <html>
            <form action="javascript:history.back(1)">
            </form>
        </html>"""
        r = build_http_response(self.url, body)
        p = RaiseHTMLParser(r)
        p.parse()
        self.assertEquals(self.url, p.forms[0].get_action())

    def test_form_multiline_tags(self):
        """
        Found this form on the wild and was unable to parse it.
        """
        resp = build_http_response(self.url, FORM_MULTILINE_TAGS)
        p = RaiseHTMLParser(resp)
        p.parse()

        self.assertEqual(1, len(p.forms))
        form = p.forms[0]

        self.assertEquals(self.url, form.get_action())
        self.assertEquals('POST', form.get_method())
        self.assertIn('input', form)
        self.assertIn('csrfmiddlewaretoken', form)

    def test_inputs_in_out_form(self):
        # We expect that the form contains all the inputs (both those declared
        # before and after). Also it must be equal to a form that includes
        # those same inputs but declared before them

        # 1st body
        body = HTML_DOC % \
            {'head': '',
             'body': (INPUT_TEXT_WITH_NAME + INPUT_TEXT_WITH_ID +
                      INPUT_FILE_WITH_NAME + INPUT_SUBMIT_WITH_NAME +
                      (FORM_WITHOUT_METHOD % {'form_content': ''}) +  # form in the middle
                      INPUT_RADIO_WITH_NAME + INPUT_CHECKBOX_WITH_NAME +
                      INPUT_HIDDEN)
             }
        resp = build_http_response(self.url, body)
        p = RaiseHTMLParser(resp)
        p.parse()

        # Only one form
        self.assertTrue(len(p.forms) == 1)
        # Ensure that parsed inputs actually belongs to the form and
        # have the expected values
        f = p.forms[0]

        self.assertEquals(['bar'], f['foo1'])         # text input
        self.assertEquals(['bar'], f['foo2'])         # text input
        self.assertEquals([''], f['foo5'])            # radio input
        self.assertEquals([''], f['foo6'])            # checkbox input
        self.assertEquals(['bar'], f['foo7'])         # hidden input
        self.assertEquals([''], f['foo4'])            # submit input
        self.assertEquals(['bar'], f['foo3'])         # file input

        # 2nd body
        body2 = HTML_DOC % \
            {'head': '',
             'body': FORM_WITHOUT_METHOD %
            {'form_content':
             INPUT_TEXT_WITH_NAME + INPUT_TEXT_WITH_ID +
             INPUT_FILE_WITH_NAME + INPUT_SUBMIT_WITH_NAME +
             INPUT_RADIO_WITH_NAME + INPUT_CHECKBOX_WITH_NAME +
             INPUT_HIDDEN
             }
             }
        resp2 = build_http_response(self.url, body2)
        p2 = RaiseHTMLParser(resp2)
        p2.parse()

        # Finally assert that the parsed forms are equals
        self.assertEquals(f, p2.forms[0])

    def test_textareas_in_out_form(self):
        body = HTML_DOC % \
            {'head': '',
             'body': (
                 TEXTAREA_WITH_ID_AND_DATA +
                 FORM_WITHOUT_METHOD %
                 {'form_content': TEXTAREA_WITH_NAME_AND_DATA} +
                 TEXTAREA_WITH_NAME_EMPTY)
             }
        resp = build_http_response(self.url, body)
        p = RaiseHTMLParser(resp)
        p.parse()

        # textarea are parsed as regular inputs
        f = p.forms[0]
        self.assertEqual(f.get('sample_id'), f.get('sample_name'))
        self.assertEqual(f.get('sample_id'), ['sample_value'])

        # Last <textarea> with empty name wasn't parsed
        self.assertEquals(2, len(f))

    def test_selects_in_out_form(self):
        # Both <select> are expected to be parsed inside the form. Because
        # they have the same name/id the same entry will be used in the form
        # although the values will be duplicated when applies.
        body = HTML_DOC % \
            {'head': '',
             'body': (
                 SELECT_WITH_NAME +
                 FORM_WITHOUT_METHOD % {'form_content': SELECT_WITH_ID} +
                 '<select><option value="xxx"/><option value="yyy"/></select>')
             }
        resp = build_http_response(self.url, body)
        p = RaiseHTMLParser(resp)
        p.parse()

        # No pending parsed selects
        self.assertEquals(0, len(p._select_option_values))

        # Only 1 select (2 have the same name); the last one is not parsed as
        # it has no name/id
        f = p.forms[0]

        # meta has all the values
        select_values = f.meta['vehicle'][0].values
        self.assertIn('car', select_values)
        self.assertIn('plane', select_values)
        self.assertIn('bike', select_values)

        # The "current" value is the first that was found
        self.assertEqual(f['vehicle'], ['car'])

        # "xxx" and "yyy" options were not parsed because they are outside the
        # form tag and doesn't have a name attribute
        self.assertNotIn('xxx', f.get_option_names())
        self.assertNotIn('yyy', f.get_option_names())

    def test_form_with_repeated_parameter_names(self):
        # Setup
        form = FORM_METHOD_POST % {'form_content':
                                   TEXTAREA_WITH_NAME_AND_DATA * 2}
        body = HTML_DOC % {'head': '',
                           'body': form}
        resp = build_http_response(self.url, body)
        p = RaiseHTMLParser(resp)

        # Run the parser
        p.parse()

        # Asserts
        self.assertEquals(1, len(p.forms))
        form = p.forms[0]

        self.assertIsInstance(form, FormParameters)
        self.assertEqual(form['sample_name'], ['sample_value',
                                               'sample_value'])

    def test_a_link_absolute(self):
        headers = Headers([('content-type', 'text/html')])
        resp = build_http_response(self.url, A_LINK_ABSOLUTE, headers=headers)
        p = RaiseHTMLParser(resp)
        p.parse()

        self.assertEquals([URL('http://w3af.com/home.php')], p.references[0])

    def test_script_tag_link_extraction(self):
        body = '''<script>window.location = "http://w3af.com/";</script>'''
        resp = build_http_response(self.url, body)
        p = RaiseHTMLParser(resp)
        p.parse()

        self.assertEquals([URL('http://w3af.com/')], p.references[1])

    def test_script_tag_link_extraction_relative(self):
        body = '''<script>window.location = "/foo.php";</script>'''
        resp = build_http_response(self.url, body)
        p = RaiseHTMLParser(resp)
        p.parse()

        self.assertEquals([URL('http://w3af.com/foo.php')], p.references[1])
