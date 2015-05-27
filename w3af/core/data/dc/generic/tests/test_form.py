# -*- coding: utf8 -*-
"""
test_form.py

Copyright 2006 Andres Riancho

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
import copy

from nose.plugins.attrib import attr

from w3af.core.data.dc.utils.token import DataToken
from w3af.core.data.dc.generic.form import Form
from w3af.core.data.parsers.utils.form_constants import INPUT_TYPE_PASSWD
from w3af.core.data.parsers.utils.form_params import FormParameters


@attr('smoke')
class TestForm(unittest.TestCase):

    def test_require_implementation(self):
        form = Form()

        self.assertRaises(NotImplementedError, form.__str__)
        self.assertRaises(NotImplementedError, form.get_type)

    def test_basic(self):
        form_params = FormParameters()
        form = Form(form_params)
        self.assertIs(form.get_form_params(), form_params)

    def test_mutant_smart_fill_simple(self):
        form_params = FormParameters()
        form_params.add_field_by_attrs({'name': 'username', 'value': ''})
        form_params.add_field_by_attrs({'name': 'address', 'value': ''})
        form_params['username'][0] = DataToken('username', '', ('username', 0))

        form = Form(form_params)

        form.smart_fill()

        self.assertEqual(form['username'], ['', ])
        self.assertEqual(form['address'], ['Bonsai Street 123', ])
        self.assertIsInstance(form['username'][0], DataToken)
        self.assertIs(form.get_form_params(), form_params)

    def test_mutant_iter_bound_tokens(self):
        form_params = FormParameters()
        form_params.add_field_by_attrs({'name': 'username',
                                        'value': '',
                                        'type': 'password'})
        form_params.add_field_by_attrs({'name': 'address', 'value': ''})

        form = Form(form_params)

        for form_copy, _ in form.iter_bound_tokens():
            self.assertIsInstance(form_copy, Form)
            self.assertEquals(form_copy.items(), form.items())
            self.assertEquals(form_copy.get_parameter_type('username'),
                              INPUT_TYPE_PASSWD)

    def test_mutant_smart_fill_with_file(self):
        form_params = FormParameters()
        form_params.add_field_by_attrs({'name': 'username', 'value': ''})
        form_params.add_field_by_attrs({'name': 'address', 'value': ''})
        form_params.add_field_by_attrs({'name': 'file', 'type': 'file'})

        form = Form(form_params)
        form['username'][0] = DataToken('username', '', ('username', 0))
        form.smart_fill()

        self.assertEqual(form['username'], ['', ])
        self.assertEqual(form['address'], ['Bonsai Street 123', ])
        self.assertIsInstance(form['username'][0], DataToken)

        str_file = form['file'][0]
        self.assertEqual(str_file.name[-4:], '.gif')
        self.assertIn('GIF', str_file)

        self.assertIs(form.get_form_params(), form_params)

    def test_login_form_utils(self):
        form_params = FormParameters()
        form_params.add_field_by_attrs({'name': 'username', 'type': 'text'})
        form_params.add_field_by_attrs({'name': 'pwd', 'type': 'password'})

        form = Form(form_params)

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

        self.assertIs(form.get_form_params(), form_params)

    def test_cpickle_simple(self):
        form_params = FormParameters()
        form_params.add_field_by_attrs({'name': 'username', 'type': 'text'})
        form_params.add_field_by_attrs({'name': 'pwd', 'type': 'password'})

        form = Form(form_params)

        pickled_form = cPickle.loads(cPickle.dumps(form))

        self.assertEqual(pickled_form.items(), form.items())

    def test_cpickle_unsync(self):
        form_params = FormParameters()
        form_params.add_field_by_attrs({'name': 'username', 'type': 'text'})
        form_params.add_field_by_attrs({'name': 'pwd', 'type': 'password'})

        form = Form(form_params)
        form['xyz'] = ['1', '2']

        pickled_form = cPickle.loads(cPickle.dumps(form))

        self.assertEqual(pickled_form.items(), form.items())

    def test_keep_sync(self):
        form_params = FormParameters()
        form_params.add_field_by_attrs({'name': 'username', 'type': 'text'})
        form_params.add_field_by_attrs({'name': 'pwd', 'type': 'password'})

        form = Form(form_params)

        self.assertNotIn('address', form_params)
        self.assertNotIn('address', form)

        # Add to the form_params
        form_params['address'] = ['']
        self.assertIn('address', form_params)
        self.assertIn('address', form)

        # Add to the Form object
        form['company'] = ['']
        self.assertIn('company', form_params)
        self.assertIn('company', form)

        # Del from the Form object
        del form['address']
        self.assertNotIn('address', form)
        self.assertNotIn('address', form_params)

        # Del from the FormParams object
        del form_params['company']
        self.assertNotIn('company', form)
        self.assertNotIn('company', form_params)

    def test_form_copy(self):
        form_params = FormParameters()
        form_params.add_field_by_attrs({'name': 'username', 'type': 'text'})
        form_params.add_field_by_attrs({'name': 'pwd', 'type': 'password'})

        form = Form(form_params)
        form.set_token(('username', 0))

        form_copy = copy.deepcopy(form)

        self.assertEqual(form.get_token(), form_copy.get_token())
        self.assertIsNot(None, form_copy.get_token())