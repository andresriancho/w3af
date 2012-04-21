import unittest

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

form_select_empty = [
    {'tagname': 'select', 'name': 'spam', 
        'options': ()
    }]

# Global container for form
ALL_FORMS = (form_with_radio, form_with_checkbox, form_select_cars)

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
                    evalue = elem['value']
                    self.assertTrue(evalue in  new_form[ename])
                    self.assertTrue(evalue in  new_form._selects[ename])

    def test_tmb_variants(self):
        # 'top-middle-bottom' mode variants
        def filter_tmb(values):
            if len(values) > 3:
                values = (values[0], values[len(values)/2], values[-1])
            return values
        
        bigform_data = form_with_radio + form_select_cars + form_select_misc
        clean_data = get_gruped_data(bigform_data)
        new_bigform = create_form_helper(bigform_data)
        total_variants = 2*3*3*3
        variants_set = set()
        
        for i, form_variant in enumerate(new_bigform.getVariants(mode="tmb")):

            if i == 0: # First element must be the created `new_bigform`
                self.assertEquals(id(new_bigform), id(form_variant))
                continue
            
            for name, values in clean_data.items():
                tmb_values = filter_tmb(values)
                self.assertTrue(form_variant[name][0] in tmb_values)
            
            variants_set.add(repr(form_variant))

        
        # Ensure we actually got the expected number of variants
        f = form.Form()
        expected = min(total_variants, f.TOP_VARIANTS)
        self.assertEquals(i, expected)
        
        # Variants shouldn't duplicated
        self.assertEquals(len(variants_set), expected)
        

    def test_all_variants(self):
        # 'all' mode variants
        bigform_data = form_with_radio + form_select_misc
        clean_data = get_gruped_data(bigform_data)
        new_bigform = create_form_helper(bigform_data)
        total_variants = 2*5*10
        variants_set = set()
        
        for i, form_variant in enumerate(new_bigform.getVariants(mode="all")):

            if i == 0: # First element must be the created `new_bigform`
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
        t_form_variants = [fv for fv in new_bigform.getVariants(mode="t")][1:]
        # Ensure we actually got the expected number of variants
        self.assertEquals(total_variants, len(t_form_variants))

        for name, values in clean_data.items():
            self.assertEquals(values[0], t_form_variants[0][name][0])
        
        # 'bottom' mode variants
        t_form_variants = [fv for fv in new_bigform.getVariants(mode="b")][1:]
        # Ensure we actually got the expected number of variants
        self.assertEquals(total_variants, len(t_form_variants))

        for name, values in clean_data.items():
            self.assertEquals(values[-1], t_form_variants[0][name][0])
        

    def test_max_variants(self):
        # Combinatoric explosion (mode="all"): total_variants = 2*5*5*5 = 
        # 250 > dc.Form.TOP_VARIANTS = 150
        new_form = create_form_helper(form_with_radio + form_select_cars + \
                                      form_select_misc)
        self.assertEquals(form.Form.TOP_VARIANTS, 
                          len([fv for fv in new_form.getVariants(mode="all")])-1)

        
    def test_same_variants_generation(self):
        # Combinatoric explosion (mode="all"): total_variants = 250 > 150
        # Therefore will be used random variants generation. We should get the
        #  same every time we call `form.getVariants`
        new_form = create_form_helper(form_with_radio + form_select_cars + \
                                      form_select_misc)
        get_all_variants = lambda: set(repr(fv) for fv in \
                                       new_form.getVariants(mode="all"))
        variants = get_all_variants()
        for i in xrange(10):
            self.assertEquals(variants, get_all_variants())

    def test_empty_select_all(self):
        '''
        This tests for handling of "select" tags that have no options inside.

        The getVariants method should return a variant with the select tag name
        that is always an empty string.

        In this case I'm going to call getVariants with mode="all"
        '''
        new_form = create_form_helper(form_with_radio + form_select_cars + \
                                      form_select_misc + form_select_empty)
        [ i for i in new_form.getVariants(mode="all") ]
        
    def test_empty_select_tb(self):
        '''
        This tests for handling of "select" tags that have no options inside.

        The getVariants method should return a variant with the select tag name
        that is always an empty string.

        In this case I'm going to call getVariants with mode="tb"

        This is the case reported by Taras at https://sourceforge.net/apps/trac/w3af/ticket/171015
        '''
        new_form = create_form_helper(form_with_radio + form_select_cars + \
                                      form_select_misc + form_select_empty)
        [ i for i in new_form.getVariants(mode="tb") ]

def get_gruped_data(form_data):
    '''
    Group form data by elem `name`. Return dict with the following structure:
    {'cars': ['volvo', 'audi', 'lada'], 'sex': ['M', 'F'], ...}
    '''
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
    Creates a dc.Form object from a dict container
    
    @param form_data: A list containing dicts representing a form's
        internal structure
    @return: A dc.Form object from `form_data`
    '''
    new_form = form.Form()
    
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
