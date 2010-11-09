
import random
import unittest

import sys
sys.path.append("/home/jandalia/workspace2/w3af")
sys.path.insert(0, "C:\Program Files\w3af\w3af")

from core.data.dc import form

form_with_radio = [
    {'tagname': 'input', 'name': 'sex', 'type': 'radio', 'value': 'male'},
    {'tagname': 'input', 'name': 'sex', 'type': 'radio', 'value': 'female'}]

# TODO: see checkbox and the `secret_value` thing
form_with_checkbox = [
{'tagname': 'input', 'name': 'vehicle', 'type': 'checkbox', 'value': 'Bike'},
{'tagname': 'input', 'name': 'vehicle', 'type': 'checkbox', 'value': 'Car'},
{'tagname': 'input', 'name': 'vehicle', 'type': 'checkbox', 'value': 'Plane'},]

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
                                                (('value', 'blue'),),
                                                (('value', 'yellow'),),
                                                (('value', 'green'),),
                                                (('value', 'red'),))},
    {'tagname': 'select', 'name': 'letters', 
                                    'options': ((('value', 'a'),), (('value', 'b'),),
                                                (('value', 'c'),), (('value', 'd'),),
                                                (('value', 'e'),), (('value', 'f'),),
                                                (('value', 'g'),), (('value', 'h'),),
                                                (('value', 'i'),), (('value', 'j'),))}
    ]

# Global container for form
ALL_FORMS = (form_with_radio, form_with_checkbox, form_select_cars)

form_four = []
form_five = []
form_six = []
form_seven = []

class test_form(unittest.TestCase):

    def test_new_form(self):
        # Create new forms and test internal structure
        for form_data in ALL_FORMS:
            new_form = create_form_helper(form_data)
            for elem in form_data:
                ename = elem['name']
                
                if elem['tagname'] == 'select':
                    self.assertTrue(set(t[0][1] for t in elem['options']) == \
                                    set(new_form._selects[ename]))
                else:
                    ivalue = elem['value']
                    self.assertTrue(ivalue in  new_form[ename])
                    self.assertTrue(ivalue in  new_form._selects[ename])

    def test_no_name(self):
        # input has no `name` attr. `id` should be used instead
        # right now not in `selects`. ask andres what about it
        pass

    def test_same_variants_generation(self):
        # When using random variants generation in we should get the same
        # variants
        pass

    def test_tmb_variants(self):
        bigform_data = form_with_radio + form_select_cars + form_select_misc
        clean_data = get_clean_data(bigform_data)
        new_bigform = create_form_helper(bigform_data)
        total_variants = 2*3*3*3
        
        for i, form_variant in enumerate(new_bigform.getVariants(mode="tmb")):

            if i == 0: # First element must be the created `new_bigform`
                self.assertEquals(id(new_bigform), id(form_variant))
                continue
            for name, values in clean_data.items():
                self.assertTrue(form_variant[name][0] in values)

        self.assertEquals(i, total_variants)

            

    def test_all_variants(self):
        pass

    def test_t_b_tb_variants(self):
        pass

    def test_max_variants(self):
        pass


def get_clean_data(form_data):
    res = {}
    for elem_data in form_data:
        values = res.setdefault(elem_data['name'], [])
        if elem_data['tagname'] == 'select':
            values += [t[0][1] for t in elem_data['options']]
        else:
            values.append(elem_data['value'])
    return res

def create_form_helper(form_data):
    '''
    Creates a dc.form object from a dict container
    
    @param form_data: A list containing dicts representing a form's
        internal structure
    @return: A dc.form object from `form_data`
    '''
    new_form = form.form()
    
    for elem_data in form_data:
        elem_type = elem_data['tagname']
        attrs = elem_data.items()
        
        if elem_type == 'input':
            type = elem_data['type']
            
            if type == 'radio':
                new_form.addRadio(attrs)
            elif type == 'checkbox':
                new_form.addCheckBox(attrs)
            else:
                pass
            
        elif elem_type == 'select':
            new_form.addSelect(elem_data['name'], elem_data['options'])
    
    return new_form


if __name__ == "__main__":
    unittest.main()
