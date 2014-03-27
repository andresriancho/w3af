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

from w3af.core.data.dc import form

form_with_radio = [
    {'tagname': 'input', 'name': 'sex', 'type': 'radio', 'value': 'male'},
    {'tagname': 'input', 'name': 'sex', 'type': 'radio', 'value': 'female'}]

# TODO: see checkbox and the `secret_value` thing
form_with_checkbox = [
    {'tagname': 'input', 'name': 'vehicle', 'type': 'checkbox',
        'value': 'Bike'},
{'tagname': 'input', 'name': 'vehicle', 'type': 'checkbox', 'value': 'Car'},
{'tagname': 'input', 'name': 'vehicle', 'type': 'checkbox', 'value': 'Plane'}, ]

form_select_cars = [
    {'tagname': 'select', 'name': 'cars',
        'options': ((('value', 'volvo'),),
                    (('value', 'saab'),),
                    (('value', 'jeep'),),
                    (('value', 'chevy'),),
                    (('value', 'fiat'),))}]

form_select_misc = [
    {'tagname': 'select', 'name': 'colors',
        'options': ((('value', 'black'),),
                    (('value', 'red'),))},
    {'tagname': 'select', 'name': 'letters',
        'options': ((('value', 'a'),), (('value', 'b'),),
                    (('value', 'g'),), (('value', 'h'),),
                    (('value', 'i'),), (('value', 'j'),))}
]

form_select_misc_large = [
    {'tagname': 'select', 'name': 'colors',
        'options': ((('value', 'black'),),
                    (('value', 'blue'),),
                    (('value', 'yellow'),),
                    (('value', 'green'),),
                    (('value', 'red'),))},
    {'tagname': 'select', 'name': 'letters',
        'options': ((('value', 'a'),), (('value', 'b'),),
                    (('value', 'c'),), (('value', 'd'),),
                    (('value', 'e'),), (('value', 'f'),),
                    (('value', 'g'),), (('value', 'h'),),
                    (('value', 'i'),), (('value', 'j'),),
                    (('value', 'k'),), (('value', 'l'),),
                    (('value', 'm'),), (('value', 'n'),))}
]

form_select_empty = [
    {'tagname': 'select', 'name': 'spam',
        'options': ()
     }]

# Global container for form
ALL_FORMS = (form_with_radio, form_with_checkbox, form_select_cars)


@attr('smoke')
class test_form(unittest.TestCase):

    def test_new_form(self):
        # Create new forms and test internal structure
        for form_data in ALL_FORMS:
            new_form = create_form_helper(form_data)
            for elem in form_data:
                ename = elem['name']

                if elem['tagname'] == 'select':
                    self.assertTrue(set(t[0][1] for t in elem['options']) ==
                                    set(new_form._selects[ename]))
                else:
                    evalue = elem['value']
                    self.assertTrue(evalue in new_form[ename])
                    self.assertTrue(evalue in new_form._selects[ename])

    def test_tmb_variants(self):
        # 'top-middle-bottom' mode variants
        def filter_tmb(values):
            if len(values) > 3:
                values = (values[0], values[len(values) / 2], values[-1])
            return values

        bigform_data = form_with_radio + form_select_misc
        clean_data = get_gruped_data(bigform_data)
        new_bigform = create_form_helper(bigform_data)
        total_variants = 2 * 2 * 3
        variants_set = set()

        for i, form_variant in enumerate(new_bigform.get_variants(mode="tmb")):

            if i == 0:  # First element must be the created `new_bigform`
                self.assertEquals(id(new_bigform), id(form_variant))
                continue

            for name, values in clean_data.items():
                tmb_values = filter_tmb(values)
                msg = 'Failed to find "%s" in "%s"' % (
                    form_variant[name][0], tmb_values)
                self.assertTrue(form_variant[name][0] in tmb_values, msg)

            variants_set.add(repr(form_variant))

        # Ensure we actually got the expected number of variants
        f = form.Form()
        expected = min(total_variants, f.TOP_VARIANTS)
        self.assertEquals(i, expected)

        # Variants shouldn't appear duplicated
        self.assertEquals(len(variants_set), expected)

    def test_tmb_variants_large(self):
        """
        Note that this test has several changes from test_tmb_variants:
            * It uses form_select_misc_large, which exceeds the form's TOP_VARIANTS = 15
            * Doesn't use filter_tmb since variants are based on a "random pick"
        """
        bigform_data = form_with_radio + form_select_cars + \
            form_select_misc_large
        clean_data = get_gruped_data(bigform_data)
        new_bigform = create_form_helper(bigform_data)
        total_variants = 2 * 3 * 3 * 3
        variants_set = set()

        # Please note that this depends completely in form.SEED AND form.TOP_VARIANTS
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
                        15: ('volvo', 'black', 'i', 'female')
                        }

        for i, form_variant in enumerate(new_bigform.get_variants(mode="tmb")):

            if i == 0:  # First element must be the created `new_bigform`
                self.assertEquals(id(new_bigform), id(form_variant))
                continue

            for name, values in clean_data.items():
                current_random_values = RANDOM_PICKS[i]
                msg = 'Failed to find "%s" in "%s"' % (
                    form_variant[name][0], current_random_values)
                self.assertTrue(
                    form_variant[name][0] in current_random_values, msg)

            variants_set.add(repr(form_variant))

        # Ensure we actually got the expected number of variants
        f = form.Form()
        expected = min(total_variants, f.TOP_VARIANTS)
        self.assertEquals(i, expected)

        # Variants shouldn't appear duplicated
        self.assertEquals(len(variants_set), expected)

    def test_all_variants(self):
        # 'all' mode variants
        bigform_data = form_with_radio + form_select_misc
        clean_data = get_gruped_data(bigform_data)
        new_bigform = create_form_helper(bigform_data)
        total_variants = 2 * 5 * 10
        variants_set = set()

        for i, form_variant in enumerate(new_bigform.get_variants(mode="all")):

            if i == 0:  # First element must be the created `new_bigform`
                self.assertEquals(id(new_bigform), id(form_variant))
                continue
            for name, all_values in clean_data.items():
                self.assertTrue(form_variant[name][0] in all_values)

            variants_set.add(repr(form_variant))

        # Ensure we actually got the expected number of variants
        f = form.Form()
        expected = min(total_variants, f.TOP_VARIANTS)
        self.assertEquals(expected, i)

        # Variants shouldn't duplicated
        self.assertEquals(expected, len(variants_set))

    def test_t_b_variants(self):
        # 'top' and 'bottom' variants
        bigform_data = form_with_radio + form_select_cars + form_select_misc
        clean_data = get_gruped_data(bigform_data)
        new_bigform = create_form_helper(bigform_data)
        total_variants = 1

        # 'top' mode variants
        t_form_variants = [fv for fv in new_bigform.get_variants(mode="t")][1:]
        # Ensure we actually got the expected number of variants
        self.assertEquals(total_variants, len(t_form_variants))

        for name, values in clean_data.items():
            self.assertEquals(values[0], t_form_variants[0][name][0])

        # 'bottom' mode variants
        t_form_variants = [fv for fv in new_bigform.get_variants(mode="b")][1:]
        # Ensure we actually got the expected number of variants
        self.assertEquals(total_variants, len(t_form_variants))

        for name, values in clean_data.items():
            self.assertEquals(values[-1], t_form_variants[0][name][0])

    def test_max_variants(self):
        # Combinatoric explosion (mode="all"): total_variants = 2*5*5*5 =
        # 250 > dc.Form.TOP_VARIANTS = 150
        new_form = create_form_helper(form_with_radio + form_select_cars +
                                      form_select_misc)
        self.assertEquals(form.Form.TOP_VARIANTS,
                          len([fv for fv in new_form.get_variants(mode="all")]) - 1)

    def test_same_variants_generation(self):
        # Combinatoric explosion (mode="all"): total_variants = 250 > 150
        # Therefore will be used random variants generation. We should get the
        #  same every time we call `form.get_variants`
        new_form = create_form_helper(form_with_radio + form_select_cars +
                                      form_select_misc)
        get_all_variants = lambda: set(repr(fv) for fv in
                                       new_form.get_variants(mode="all"))
        variants = get_all_variants()
        for i in xrange(10):
            self.assertEquals(variants, get_all_variants())

    def test_empty_select_all(self):
        """
        This tests for handling of "select" tags that have no options inside.

        The get_variants method should return a variant with the select tag name
        that is always an empty string.

        In this case I'm going to call get_variants with mode="all"
        """
        new_form = create_form_helper(form_with_radio + form_select_cars +
                                      form_select_misc + form_select_empty)
        [i for i in new_form.get_variants(mode="all")]

    def test_empty_select_tb(self):
        """
        This tests for handling of "select" tags that have no options inside.

        The get_variants method should return a variant with the select tag name
        that is always an empty string.

        In this case I'm going to call get_variants with mode="tb"

        This is the case reported by Taras at https://sourceforge.net/apps/trac/w3af/ticket/171015
        """
        new_form = create_form_helper(form_with_radio + form_select_cars +
                                      form_select_misc + form_select_empty)
        [i for i in new_form.get_variants(mode="tb")]

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
        form_data = [{'tagname': 'input', 'type':'text', 'name':
                      'abc', 'value':'123'}]
        new_form = create_form_helper(form_data)
        self.assertEqual(str(new_form), 'abc=123')

    def test_form_str_simple_2(self):
        form_data = [{'tagname': 'input', 'type':'text', 'name':'abc', 'value':'123'},
                     {'tagname': 'input', 'type':'hidden', 'name':'def', 'value':'000'}]
        new_form = create_form_helper(form_data)
        self.assertEqual(str(new_form), 'abc=123&def=000')

    def test_form_str_special_chars(self):
        form_data = [{'tagname': 'input', 'type':'text', 'name':'v', 'value':'áéíóú'},
                     {'tagname': 'input', 'type':'hidden', 'name':'c', 'value':'ñçÑÇ'}]
        new_form = create_form_helper(form_data)
        new_form.add_submit('address', 'bsas')
        self.assertEqual(urllib.unquote(str(new_form)).decode('utf-8'),
                         u'c=ñçÑÇ&address=bsas&v=áéíóú')

    def test_form_str_radio_select(self):
        new_form = create_form_helper(form_with_radio + form_with_checkbox +
                                      form_select_cars)
        self.assertEqual(str(new_form), 'cars=fiat&sex=male&vehicle=Bike')


def get_gruped_data(form_data):
    """
    Group form data by elem `name`. Return dict with the following structure:
    {'cars': ['volvo', 'audi', 'lada'], 'sex': ['M', 'F'], ...}
    """
    res = {}
    for elem_data in form_data:
        values = res.setdefault(elem_data['name'], [])
        if elem_data['tagname'] == 'select':
            values += [t[0][1] for t in elem_data['options']]
        else:
            values.append(elem_data['value'])
    return res


def create_form_helper(form_data):
    """
    Creates a dc.Form object from a dict container

    :param form_data: A list containing dicts representing a form's
        internal structure
    :return: A dc.Form object from `form_data`
    """
    new_form = form.Form()

    for elem_data in form_data:
        elem_type = elem_data['tagname']
        attrs = elem_data.items()

        if elem_type == 'input':
            _type = elem_data['type']

            if _type == 'radio':
                new_form.add_radio(attrs)
            elif _type == 'checkbox':
                new_form.add_check_box(attrs)
            elif _type in ('text', 'hidden'):
                new_form.add_input(attrs)

        elif elem_type == 'select':
            new_form.add_select(elem_data['name'], elem_data['options'])

    return new_form
