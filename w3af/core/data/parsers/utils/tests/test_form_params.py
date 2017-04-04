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
import copy
import cPickle

from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.utils.form_constants import (MODE_ALL, MODE_TB,
                                                         MODE_B, MODE_T,
                                                         MODE_TMB,
                                                         INPUT_TYPE_RADIO,
                                                         INPUT_TYPE_SELECT)
from w3af.core.data.parsers.utils.form_params import (FormParameters,
                                                      DEFAULT_FORM_ENCODING)


form_with_radio = [{'name': 'sex', 'type': 'radio', 'value': 'male'},
                   {'name': 'sex', 'type': 'radio', 'value': 'female'}]

# TODO: see checkbox and the `secret_value` thing
form_with_checkbox = [{'name': 'vehicle', 'type': 'checkbox', 'value': 'Bike'},
                      {'name': 'vehicle', 'type': 'checkbox', 'value': 'Car'},
                      {'name': 'vehicle', 'type': 'checkbox', 'value': 'Plane'}]

form_select_cars = [
    {'type': 'select', 'name': 'cars',
     'values': ('volvo', 'saab', 'jeep', 'chevy', 'fiat')}]

form_select_misc = [
    {'type': 'select', 'name': 'colors', 'values': ('black', 'red')},
    {'type': 'select', 'name': 'letters', 'values': ('a', 'b', 'g', 'h',
                                                     'i', 'j')}
]

form_select_misc_large = [
    {'type': 'select', 'name': 'colors',
     'values': ('black', 'blue', 'yellow', 'green', 'red')},

    {'type': 'select', 'name': 'letters', 'values': ('a', 'b', 'c', 'd',
                                                     'e', 'f', 'g', 'h',
                                                     'i', 'j', 'k', 'l',
                                                     'm', 'n')}
]

form_select_empty = [{'type': 'select', 'name': 'spam', 'values': ()}]

# Global container for form
ALL_FORMS = (form_with_radio, form_with_checkbox, form_select_cars)


class TestFormParams(unittest.TestCase):
    def test_set_action_str(self):
        f = FormParameters()
        self.assertRaises(TypeError, f.set_action, 'http://www.w3af.com/')

    def test_set_action_url(self):
        f = FormParameters()
        action = URL('http://www.w3af.com/')
        f.set_action(action)

        self.assertIs(f.get_action(), action)

    def test_set_form_encoding(self):
        f = FormParameters()
        f.set_form_encoding(DEFAULT_FORM_ENCODING)

        self.assertIs(f.get_form_encoding(), DEFAULT_FORM_ENCODING)

    def test_new_form(self):
        """
        Create new forms and test internal structure
        """
        for form_data in ALL_FORMS:
            # Create the form
            new_form = create_form_params_helper(form_data)

            for elem in form_data:
                elem_name = elem.get('name', None)
                elem_type = elem.get('type', None)

                values = new_form.get(elem_name)

                form_input_type = new_form.get_parameter_type(elem_name)
                self.assertEqual(form_input_type, elem_type)

                # pylint: disable=E1133
                for value in values:
                    if elem_type == INPUT_TYPE_SELECT:
                        self.assertIn(value, elem['values'])
                # pylint: enable=E1133

    def test_variants_do_not_modify_original(self):
        bigform_data = form_with_radio + form_select_misc
        form = create_form_params_helper(bigform_data)
        orig_items = form.items()

        # Generate the variants
        variants = [v for v in form.get_variants(mode=MODE_TMB)]

        self.assertEqual(orig_items, form.items())

    def test_tmb_variants(self):
        # 'top-middle-bottom' mode variants
        def filter_tmb(values):
            if len(values) > 3:
                values = (values[0],
                          values[len(values) / 2],
                          values[-1])
            return values

        bigform_data = form_with_radio + form_select_misc
        clean_data = get_grouped_data(bigform_data)
        new_bigform = create_form_params_helper(bigform_data)
        total_variants = 2 * 2 * 3
        variants_set = set()
        variants = [v for v in new_bigform.get_variants(mode=MODE_TMB)]

        for i, form_variant in enumerate(variants):

            # First element must be the created `new_bigform`
            if i == 0:
                self.assertIs(new_bigform, form_variant)
                continue

            for name, values in clean_data.items():
                tmb_values = filter_tmb(values)
                self.assertIn(form_variant[name][0], tmb_values)

            variants_set.add(repr(form_variant))

        # Ensure we actually got the expected number of variants
        f = FormParameters()
        self.assertEquals(len(variants), total_variants + 1)

        # Variants shouldn't appear duplicated
        self.assertEquals(len(variants_set), total_variants)

    def test_tmb_variants_large(self):
        """
        Note that this test has several changes from test_tmb_variants:

            * It uses form_select_misc_large, which exceeds the form's
              TOP_VARIANTS = 15

            * Doesn't use filter_tmb since variants are based on a "random pick"
        """
        bigform_data = (form_with_radio +
                        form_select_cars +
                        form_select_misc_large)
        clean_data = get_grouped_data(bigform_data)
        new_bigform = create_form_params_helper(bigform_data)
        # total_variants = 2 * 3 * 3 * 3
        variants_set = set()
        variants = [v for v in new_bigform.get_variants(mode=MODE_TMB)]

        # Please note that this depends completely in form.SEED AND
        # form.TOP_VARIANTS
        RANDOM_PICKS = {1: ('volvo', 'black', 'd', 'female'),
                        2: ('volvo', 'blue', 'i', 'male'),
                        3: ('volvo', 'blue', 'f', 'female'),
                        4: ('volvo', 'black', 'g', 'female'),
                        5: ('volvo', 'black', 'm', 'male'),
                        6: ('volvo', 'black', 'l', 'male'),
                        7: ('volvo', 'blue', 'b', 'female'),
                        8: ('volvo', 'blue', 'e', 'female'),
                        9: ('volvo', 'black', 'c', 'male'),
                        10: ('volvo', 'black', 'a', 'female'),
                        11: ('volvo', 'blue', 'e', 'male'),
                        12: ('volvo', 'black', 'j', 'male'),
                        13: ('volvo', 'blue', 'c', 'male'),
                        14: ('volvo', 'black', 'a', 'male'),
                        15: ('volvo', 'black', 'i', 'female')}

        for i, form_variant in enumerate(variants):

            # First element must be the created `new_bigform`
            if i == 0:
                self.assertIs(new_bigform, form_variant)
                continue

            option = []
            for name, values in clean_data.items():
                form_value = form_variant[name][0]
                option.append(form_value)

            current_option = RANDOM_PICKS[i]
            self.assertEqual(tuple(option), current_option)

            variants_set.add(repr(form_variant))

        # Ensure we actually got the expected number of variants
        f = FormParameters()
        self.assertEquals(len(variants), f.TOP_VARIANTS + 1)

        # Variants shouldn't appear duplicated
        self.assertEquals(len(variants_set), f.TOP_VARIANTS)

    def test_all_variants(self):
        # 'all' mode variants
        bigform_data = form_with_radio + form_select_misc
        clean_data = get_grouped_data(bigform_data)
        new_bigform = create_form_params_helper(bigform_data)
        total_variants = 2 * 5 * 10
        variants_set = set()

        for i, form_variant in enumerate(new_bigform.get_variants(mode=MODE_ALL)):

            # First element must be the created `new_bigform`
            if i == 0:
                self.assertIs(new_bigform, form_variant)
                continue

            for name, all_values in clean_data.items():
                self.assertIn(form_variant[name][0], all_values)

            variants_set.add(repr(form_variant))

        # Ensure we actually got the expected number of variants
        f = FormParameters()
        expected = min(total_variants, f.TOP_VARIANTS)
        self.assertEquals(expected, i)

        # Variants shouldn't duplicated
        self.assertEquals(expected, len(variants_set))

    def test_t_b_variants(self):
        # 'top' and 'bottom' variants
        bigform_data = form_with_radio + form_select_cars + form_select_misc
        clean_data = get_grouped_data(bigform_data)
        new_bigform = create_form_params_helper(bigform_data)
        total_variants = 1

        # 'top' mode variants
        t_form_variants = [fv for fv in new_bigform.get_variants(mode=MODE_T)][1:]
        # Ensure we actually got the expected number of variants
        self.assertEquals(total_variants, len(t_form_variants))

        for name, values in clean_data.items():
            self.assertEquals(values[0], t_form_variants[0][name][0])

        # 'bottom' mode variants
        t_form_variants = [fv for fv in new_bigform.get_variants(mode=MODE_B)][1:]
        # Ensure we actually got the expected number of variants
        self.assertEquals(total_variants, len(t_form_variants))

        for name, values in clean_data.items():
            self.assertEquals(values[-1], t_form_variants[0][name][0])

    def test_max_variants(self):
        # Combinatoric explosion (mode=MODE_ALL): total_variants = 2*5*5*5 =
        # 250 > dc.Form.TOP_VARIANTS = 150
        new_form = create_form_params_helper(form_with_radio +
                                             form_select_cars +
                                             form_select_misc)
        self.assertEquals(FormParameters.TOP_VARIANTS,
                          len([fv for fv in new_form.get_variants(mode=MODE_ALL)]) - 1)

    def test_same_variants_generation(self):
        # Combinatoric explosion (mode=MODE_ALL): total_variants = 250 > 150
        #
        # Therefore will be used random variants generation. We should get the
        # same every time we call `form.get_variants`
        new_form = create_form_params_helper(form_with_radio +
                                             form_select_cars +
                                             form_select_misc)
        get_all_variants = lambda: set(repr(fv) for fv in
                                       new_form.get_variants(mode=MODE_ALL))
        variants = get_all_variants()
        for i in xrange(10):
            self.assertEquals(variants, get_all_variants())

    def test_empty_select_all(self):
        """
        This tests for handling of "select" tags that have no options inside.

        The get_variants method should return a variant with the select tag name
        that is always an empty string.

        In this case I'm going to call get_variants with mode=MODE_ALL
        """
        new_form = create_form_params_helper(form_with_radio +
                                             form_select_cars +
                                             form_select_misc +
                                             form_select_empty)
        [i for i in new_form.get_variants(mode=MODE_ALL)]

    def test_empty_select_tb(self):
        """
        This tests for handling of "select" tags that have no options inside.

        The get_variants method should return a variant with the select tag name
        that is always an empty string.

        In this case I'm going to call get_variants with mode=MODE_TB

        This is the case reported by Taras at https://sourceforge.net/apps/trac/w3af/ticket/171015
        """
        new_form = create_form_params_helper(form_with_radio +
                                             form_select_cars +
                                             form_select_misc +
                                             form_select_empty)
        [i for i in new_form.get_variants(mode=MODE_TB)]

    def test_form_params_deepish_copy(self):
        form = create_form_params_helper(form_with_radio + form_with_checkbox)
        copy = form.deepish_copy()

        self.assertEqual(form.items(), copy.items())
        self.assertEqual(form._method, copy._method)
        self.assertEqual(form._action, copy._action)

        self.assertIsNot(form, copy)
        self.assertEquals(copy.get_parameter_type('sex'), INPUT_TYPE_RADIO)

    def test_form_params_deep_copy(self):
        form = create_form_params_helper(form_with_radio + form_with_checkbox)
        form_copy = copy.deepcopy(form)

        self.assertEqual(form.items(), form_copy.items())
        self.assertEqual(form._method, form_copy._method)
        self.assertEqual(form._action, form_copy._action)
        self.assertEqual(form._autocomplete, form_copy._autocomplete)

        self.assertIsNot(form, copy)
        self.assertEquals(form_copy.get_parameter_type('sex'), INPUT_TYPE_RADIO)

    def test_login_form_utils(self):
        form = FormParameters()
        form.add_field_by_attrs({'name': 'username', 'type': 'text'})
        form.add_field_by_attrs({'name': 'pwd', 'type': 'password'})

        self.assertTrue(form.is_login_form())
        self.assertFalse(form.is_registration_form())
        self.assertFalse(form.is_password_change_form())
        self.assertEqual(form.get_parameter_type_count(), (1, 1, 0))

    def test_pickle(self):
        form = create_form_params_helper(form_with_radio + form_with_checkbox)

        pickled_form_params = cPickle.loads(cPickle.dumps(form))

        self.assertEqual(pickled_form_params.items(), form.items())
        self.assertIsNot(form, copy)
        self.assertEquals(pickled_form_params.get_parameter_type('sex'),
                          INPUT_TYPE_RADIO)

    def test_get_form_id(self):
        action = URL('http://www.w3af.com/action')
        hosted_at_url = URL('http://www.w3af.com/')
        attributes = {'class': 'form-main'}

        form = FormParameters(method='GET', action=action,
                              attributes=attributes,
                              hosted_at_url=hosted_at_url)
        form.add_field_by_attrs({'name': 'username', 'type': 'text'})
        form.add_field_by_attrs({'name': 'pwd', 'type': 'password'})

        form_id = form.get_form_id()

        self.assertEqual(form_id.action, action)
        self.assertEqual(form_id.attributes, attributes)
        self.assertEqual(form_id.method, 'GET')
        self.assertEqual(form_id.hosted_at_url, hosted_at_url)
        self.assertEqual(form_id.inputs, ['username', 'pwd'])


def get_grouped_data(form_data):
    """
    Group form data by elem `name`.

    :return: dict with the following structure:

        {'cars': ['volvo', 'audi', 'lada'],
         'sex': ['M', 'F'], ...}

    """
    res = {}

    for elem_data in form_data:
        values = res.setdefault(elem_data['name'], [])
        if elem_data['type'] == INPUT_TYPE_SELECT:
            values.extend(elem_data['values'])
        else:
            values.append(elem_data['value'])

    return res


def create_form_params_helper(form_data):
    """
    Creates a dc.Form object from a dict container

    :param form_data: A list containing dicts representing a form's
        internal structure
    :return: A dc.Form object from `form_data`
    """
    new_form_params = FormParameters()

    for elem_data in form_data:
        new_form_params.add_field_by_attrs(elem_data)

    return new_form_params
