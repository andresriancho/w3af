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

from nose.plugins.attrib import attr

from w3af.core.data.dc.urlencoded_form import URLEncodedForm
from w3af.core.data.dc.utils.token import DataToken


@attr('smoke')
class TestForm(unittest.TestCase):

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
        form_with_plus = [
            {'tagname': 'input', 'name': 'foo', 'type':
                'hidden', 'value': 'bar+spam'},
            {'tagname': 'input', 'name': 'eggs', 'type': 'text'}]

        new_form = create_form_helper(form_with_plus)
        self.assertEqual(str(new_form), 'eggs=&foo=bar%2Bspam')

    def test_form_str_simple(self):
        form_data = [{'tagname': 'input',
                      'type': 'text',
                      'name': 'abc',
                      'value': '123'}]
        new_form = create_form_helper(form_data)
        self.assertEqual(str(new_form), 'abc=123')

    def test_form_str_simple_2(self):
        form_data = [{'tagname': 'input',
                      'type': 'text',
                      'name': 'abc',
                      'value': '123'},
                     {'tagname': 'input',
                      'type': 'hidden',
                      'name': 'def',
                      'value': '000'}]
        new_form = create_form_helper(form_data)
        self.assertEqual(str(new_form), 'abc=123&def=000')

    def test_form_str_special_chars_1(self):
        form_data = [{'tagname': 'input',
                      'type': 'text',
                      'name': 'abc',
                      'value': '1"2'}]
        new_form = create_form_helper(form_data)
        self.assertEqual(str(new_form), 'abc=1%222')

    def test_form_str_special_chars_2(self):
        form_data = [{'tagname': 'input',
                      'type': 'text',
                      'name': 'v',
                      'value': 'áéíóú'},
                     {'tagname': 'input',
                      'type': 'hidden',
                      'name': 'c',
                      'value': 'ñçÑÇ'}]
        new_form = create_form_helper(form_data)
        new_form.add_submit('address', 'bsas')
        self.assertEqual(urllib.unquote(str(new_form)).decode('utf-8'),
                         u'c=ñçÑÇ&address=bsas&v=áéíóú')

    def test_form_str_radio_select(self):
        new_form = create_form_helper(form_with_radio + form_with_checkbox +
                                      form_select_cars)
        self.assertEqual(str(new_form), 'cars=fiat&sex=male&vehicle=Bike')

    def test_mutant_smart_fill_simple(self):
        form = Form()
        form.add_input([("name", "username"), ("value", "")])
        form.add_input([("name", "address"), ("value", "")])
        form['username'][0] = token = DataToken('username', '')

        form.smart_fill()

        self.assertEqual(form['username'], ['', ])
        self.assertEqual(form['address'], ['Bonsai Street 123', ])
        self.assertIsInstance(form['username'][0], DataToken)

    def test_mutant_smart_fill_with_file(self):
        form = Form()
        form.add_input([("name", "username"), ("value", "")])
        form.add_input([("name", "address"), ("value", "")])
        form.add_file_input([("name", "file"), ("type", "file")])
        form['username'][0] = token = DataToken('username', '')

        form.smart_fill()

        self.assertEqual(form['username'], ['', ])
        self.assertEqual(form['address'], ['Bonsai Street 123', ])
        self.assertIsInstance(form['username'][0], DataToken)

        str_file = form['file'][0]
        self.assertEqual(str_file.name[-4:], '.gif')
        self.assertIn('GIF', str_file)

    def test_login_form_utils(self):
        form = Form()
        form.add_input([("name", "username"), ("type", "text")])
        form.add_input([("name", "pwd"), ("type", "password")])

        self.assertTrue(form.is_login_form())
        self.assertFalse(form.is_registration_form())
        self.assertFalse(form.is_password_change_form())
        self.assertEqual(form.get_parameter_type_count(), (1, 1, 0))

        user_token, pass_token = form.get_login_tokens()
        self.assertEqual(user_token.get_name(), 'username')
        self.assertEqual(pass_token.get_name(), 'pwd')
        self.assertEqual(user_token.get_value(), '')
        self.assertEqual(pass_token.get_value(), '')

        form.set_login_username('andres')
        self.assertEqual(form['username'][0], 'andres')
        self.assertEqual(form['pwd'][0], '')

        form.set_login_username('pablo')
        form.set_login_password('long-complex')
        self.assertEqual(form['username'][0], 'pablo')
        self.assertEqual(form['pwd'][0], 'long-complex')




