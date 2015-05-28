# -*- coding: UTF-8 -*-
"""
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
import urllib
import copy
import cPickle

from nose.plugins.attrib import attr

from w3af.core.data.dc.urlencoded_form import URLEncodedForm
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.utils.form_constants import INPUT_TYPE_TEXT
from w3af.core.data.parsers.utils.tests.test_form_params import (form_with_radio,
                                                                 form_with_checkbox,
                                                                 form_select_cars,
                                                                 create_form_params_helper)


@attr('smoke')
class TestURLEncodedForm(unittest.TestCase):

    def test_from_postdata_no_encoding(self):
        headers = Headers()
        post_data = 'a=2&c=3'
        self.assertRaises(ValueError, URLEncodedForm.from_postdata, headers,
                          post_data)

    def test_from_postdata_no_post_data(self):
        headers = Headers([('content-type', URLEncodedForm.ENCODING)])
        post_data = ''

        form = URLEncodedForm.from_postdata(headers, post_data)

        self.assertEqual(len(form), 0)

    def test_from_postdata_ok(self):
        headers = Headers([('content-type', URLEncodedForm.ENCODING)])
        post_data = 'a=2&c=3'

        form = URLEncodedForm.from_postdata(headers, post_data)

        self.assertEqual(form['a'], ['2'])
        self.assertEqual(form['c'], ['3'])

        self.assertFalse(form.is_login_form())
        self.assertFalse(form.is_password_change_form())
        self.assertFalse(form.is_registration_form())

        self.assertEqual(form.get_parameter_type('a'), INPUT_TYPE_TEXT)
        self.assertEqual(form.get_parameter_type('b'), INPUT_TYPE_TEXT)

    def test_form_with_plus_value(self):
        """
        This test verifies that a fix for the bug identified while scanning
        demo.testfire.net is still working as expected. The issue was that the
        site had a form that looked like:

        <form action="/xyz">
            <intput name="foo" value="bar+spam" type="hidden">
            <intput name="eggs" type="text">
            ...
        </form>

        And when trying to send a request to that form the "+" in the value
        was sent as %20. The input was an .NET's EVENTVALIDATION thus it was
        impossible to find any bugs in the "eggs" parameter.

        Please note that this is just a partial test, since there is much more
        going on in w3af than just creating a form and encoding it. A functional
        test for this issue can be found at test_special_chars.py
        """
        form_with_plus = [{'tagname': 'input', 'name': 'foo', 'type':
                           'hidden', 'value': 'bar+spam'},
                          {'tagname': 'input', 'name': 'eggs', 'type': 'text'}]

        form = URLEncodedForm(create_form_params_helper(form_with_plus))
        self.assertEqual(str(form), 'eggs=&foo=bar%2Bspam')

    def test_form_str_simple(self):
        form_data = [{'tagname': 'input',
                      'type': 'text',
                      'name': 'abc',
                      'value': '123'}]
        form = URLEncodedForm(create_form_params_helper(form_data))
        self.assertEqual(str(form), 'abc=123')

    def test_form_str_simple_2(self):
        form_data = [{'tagname': 'input',
                      'type': 'text',
                      'name': 'abc',
                      'value': '123'},
                     {'tagname': 'input',
                      'type': 'hidden',
                      'name': 'def',
                      'value': '000'}]
        form = URLEncodedForm(create_form_params_helper(form_data))
        self.assertEqual(str(form), 'abc=123&def=000')

    def test_form_str_special_chars_1(self):
        form_data = [{'tagname': 'input',
                      'type': 'text',
                      'name': 'abc',
                      'value': '1"2'}]
        form = URLEncodedForm(create_form_params_helper(form_data))
        self.assertEqual(str(form), 'abc=1%222')

    def test_form_str_special_chars_2(self):
        form_data = [{'tagname': 'input',
                      'type': 'text',
                      'name': 'v',
                      'value': 'áéíóú'},
                     {'tagname': 'input',
                      'type': 'hidden',
                      'name': 'c',
                      'value': 'ñçÑÇ'}]

        form_params = create_form_params_helper(form_data)
        form_params.add_field_by_attrs({'name': 'address', 'value': 'bsas'})

        form = URLEncodedForm(form_params)

        self.assertEqual(urllib.unquote(str(form)).decode('utf-8'),
                         u'c=ñçÑÇ&address=bsas&v=áéíóú')

    def test_form_str_radio_select(self):
        form_dict = form_with_radio + form_with_checkbox + form_select_cars
        form = URLEncodedForm(create_form_params_helper(form_dict))
        self.assertEqual(str(form), 'cars=volvo&vehicle=Bike&sex=male')

    def test_form_copy(self):
        headers = Headers([('content-type', URLEncodedForm.ENCODING)])
        post_data = 'a=2&c=3'

        form = URLEncodedForm.from_postdata(headers, post_data)
        form.set_token(('a', 0))

        form_copy = copy.deepcopy(form)

        self.assertEqual(form, form_copy)
        self.assertEqual(form.get_token(), form_copy.get_token())
        self.assertIsNot(None, form_copy.get_token())

    def test_form_pickle(self):
        headers = Headers([('content-type', URLEncodedForm.ENCODING)])
        post_data = 'a=2&c=3'

        form = URLEncodedForm.from_postdata(headers, post_data)
        form.set_token(('a', 0))

        pickled_form = cPickle.dumps(form)
        unpickled_form = cPickle.loads(pickled_form)

        self.assertEqual(form, unpickled_form)
        self.assertEqual(form.get_token(), unpickled_form.get_token())
        self.assertIsNotNone(unpickled_form.get_token())
        self.assertEqual(unpickled_form.keys(), ['a', 'c'])
