#!/usr/bin/env python

import os
import sys
import getopt
import hashlib
import random

from jinja2 import Template


USAGE = '''\
Usage:

    ./build-crawl-test.py --pages=200 --parameters-per-page=0.3 --forms=0.1 --form-params=3 --output=site/

Description:

    Creates a new site which is useful for testing the crawler. The site will
    contain multiple linked pages with forms, parameters, images, etc.
    
    After creating the site you can:
    
        cd site/
        python -m SimpleHTTPServer 8000
        
    And run a w3af scan against http://localhost:8000/ . 
    
    The tool is deterministic: will always generate the same site for the same 
    parameter names, so it is something you can use for unittests.

Parameters:

    - pages: The number of pages (links) to create
    
    - parameters-per-page: The number of query string parameters that each page
                           should have. Using a number between 0 and 1 will make
                           the tool create parameters in N% of the pages.
                           
    - forms: The number of forms to include per page
    
    - form-params: The number of parameters to include in each form
    
    - output: The output directory where all the files will be created
'''


def _main():

    long_params = ['pages=',
                   'parameters-per-page=',
                   'forms=',
                   'form-params=',
                   'output=']

    options, remainder = getopt.getopt(sys.argv[1:], 'p:q:f:g:o', long_params)

    pages = None
    parameters_per_page = None
    forms = None
    form_params = None
    output = None

    for opt, arg in options:
        if opt in ('-p', '--pages'):
            pages = arg
        elif opt in ('-q', '--parameters-per-page'):
            parameters_per_page = arg
        elif opt in ('-f', '--forms'):
            forms = arg
        elif opt in ('-g', '--form-params'):
            form_params = arg
        elif opt in ('-o', '--output'):
            output = arg

    try:
        pages = int(pages)
        assert pages >= 1
    except:
        print('Error in --pages parameter')
        print('')
        print(USAGE)
        sys.exit(1)

    try:
        parameters_per_page = float(parameters_per_page)
        assert parameters_per_page > 0
    except:
        print('Error in --parameters-per-page parameter')
        print('')
        print(USAGE)
        sys.exit(1)

    try:
        forms = float(forms)
        assert forms > 0
    except:
        print('Error in --forms parameter')
        print('')
        print(USAGE)
        sys.exit(1)

    try:
        form_params = float(form_params)
        assert form_params >= 1
    except:
        print('Error in --form-params parameter')
        print('')
        print(USAGE)
        sys.exit(1)

    try:
        assert output is not None
        assert os.path.exists(output)
        assert os.path.isdir(output)
    except:
        print('Error in --output parameter')
        print('')
        print(USAGE)
        sys.exit(1)

    generate_site(pages, parameters_per_page, forms, form_params, output)
    sys.exit(0)


PAGE_TEMPLATE = Template('''\
<html>
    <head>
        <title>{{ title }}</title>
    </head>
    
    <body>
        {% for href in hrefs %}
        <a href="{{ href }}">{{ href }}</a><br/>
        {% endfor %}
        
        <br/>
        
        {% for form in forms %}
        <form action="{{ form.action }}" method="GET">
            {% for param in form.params %}
            {{ param }}: <input name="{{ param }}" type="text"></input><br/>
            {% endfor %}
            
            <input type="submit">
        </form>
        {% endfor %}
    </body>
</html>
''')


class Form(object):
    def __init__(self, action, params):
        self.action = action
        self.params = params


def render(title, hrefs, forms):
    return PAGE_TEMPLATE.render(title=title,
                                hrefs=hrefs,
                                forms=forms)


def render_index_html(href):
    template = Template('<a href="{{ href }}">{{ href }}</a>')
    return template.render(href=href)


def generate_page_path(page_num):
    return generate_identifier(page_num, 'PATH')


def generate_page_filename(page_num):
    return generate_identifier(page_num, 'FILENAME') + '.html'


def generate_parameter_name(page_num, form_num, param_num):
    param_id = '%s-%s-%s' % (page_num, form_num, param_num)
    return generate_identifier(param_id, 'PARAMETER')


def generate_identifier(num, _type):
    md5 = hashlib.md5()
    md5.update(_type + str(num))
    return md5.hexdigest()[:10]


def build_href(page_path, page_filename, qs):
    if qs:
        return '/' + page_path + '/' + page_filename + '?' + qs
    else:
        return '/' + page_path + '/' + page_filename


def get_query_string_for_page(page_num, parameters_per_page):
    parameters_per_page = get_probabilistic_count(parameters_per_page)

    query_string = []

    for qs_num in xrange(int(parameters_per_page)):
        param_name = generate_parameter_name(page_num, qs_num, qs_num)
        param_value = '1'

        query_string.append('%s=%s' % (param_name, param_value))

    return '&'.join(query_string)


def generate_index_html(output):
    page_path = generate_page_path(0)
    page_filename = generate_page_filename(0)

    href = '/' + page_path + '/' + page_filename

    index_html = render_index_html(href)

    file(os.path.join(output, 'index.html'), 'w').write(index_html)


def get_probabilistic_count(count):
    integer = int(count)

    if integer == count:
        return integer

    decimal_part = count - integer
    decimal_part *= 100

    print random.randint(0, 100) , decimal_part
    if random.randint(0, 100) > decimal_part:
        return integer + 1

    return integer


def generate_site(pages, parameters_per_page, forms, form_params, output):

    random.seed(1)

    generate_index_html(output)

    for page_num in xrange(pages):
        #
        # Where will we save the page in the local file system?
        #
        page_path = generate_page_path(page_num)
        page_filename = generate_page_filename(page_num)

        os.mkdir(os.path.join(output, page_path))
        output_file = os.path.join(output, page_path, page_filename)

        #
        # Define the title
        #
        title = page_filename

        #
        # Where will this page link to?
        #
        href_num_1 = random.randint(0, pages)
        page_path_1 = generate_page_path(href_num_1)
        page_filename_1 = generate_page_filename(href_num_1)
        qs_1 = get_query_string_for_page(href_num_1, parameters_per_page)
        href_1 = build_href(page_path_1, page_filename_1, qs_1)

        href_num_2 = random.randint(0, pages)
        page_path_2 = generate_page_path(href_num_2)
        page_filename_2 = generate_page_filename(href_num_2)
        qs_2 = get_query_string_for_page(href_num_2, parameters_per_page)
        href_2 = build_href(page_path_2, page_filename_2, qs_2)

        hrefs = [href_1, href_2]

        forms_i = get_probabilistic_count(forms)
        form_params_i = get_probabilistic_count(form_params)

        #
        # Build the forms for this page
        #
        generated_forms = []

        for form_num in xrange(int(forms_i)):
            action_num = random.randint(0, pages)

            form_path = generate_page_path(action_num)
            form_filename = generate_page_filename(action_num)
            action = '/' + form_path + '/' + form_filename

            params = [generate_parameter_name(page_num, form_num, i) for i in xrange(int(form_params_i))]

            generated_forms.append(Form(action, params))

        page_content = render(title, hrefs, generated_forms)
        file(output_file, 'w').write(page_content)


if __name__ == "__main__":
    _main()
