# -*- coding: UTF-8 -*-
"""
test_sgmlparsers.py

Copyright 2011 Andres Riancho

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
import os
import unittest
import cPickle

from functools import partial
from itertools import combinations
from random import choice

from nose.plugins.attrib import attr
from nose.plugins.skip import SkipTest

from w3af import ROOT_PATH
from w3af.core.data.parsers.utils.form_params import FormParameters
from w3af.core.data.parsers.html import HTMLParser
from w3af.core.data.parsers.sgml import SGMLParser
from w3af.core.data.parsers.url import URL
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.url.tests.test_HTTPResponse import TEST_RESPONSES
from w3af.core.data.dc.headers import Headers


HTML_DOC = u"""
<html>
    <head>
        %(head)s
    </head>
    <body>
        %(body)s
    </body>
</html>
"""

# Form templates
FORM_METHOD_GET = u"""
<form method="GET" action="/index.php">
    %(form_content)s
</form>
"""
FORM_METHOD_POST = u"""
<form method="POST" action="/index.php">
    %(form_content)s
</form>
"""
FORM_WITHOUT_METHOD = u"""
<form action="/index.php">
    %(form_content)s
</form>
"""
FORM_WITHOUT_ACTION = u"""
<form method="POST">
    %(form_content)s
</form>
"""

FORM_MULTILINE_TAGS = u"""
<form  class="form-horizontal" method="post" ><input type='hidden' name='csrfmiddlewaretoken' value='UN2BDAoRUTtlWlFtNCTFtjLZsLRYQQ1E' /> <div id="div_id_input" class="control-group"><label for="id_input" class="control-label requiredField">
                What is your favorite food?<span class="asteriskField">*</span></label><div class="controls"><input class="form-control input-sm textinput textInput" id="id_input" maxlength="40" name="input" type="text" value="Burgers" /> </div></div><div  
      style="padding: 10px;"><i class="icon-leaf"></i> Hint: <code>&lt;script&gt;alert(1)&lt;/script&gt;</code></div><div class="form-actions"><input type="submit"
    name="/xss"
    value="Submit"
    
        class="btn btn-primary btn-info pull-right"
        id="submit-id-xss"
    
    
    /> </div></form>
"""

# Textarea templates
TEXTAREA_WITH_NAME_AND_DATA = u"""
<textarea name="sample_name">
    sample_value
</textarea>"""
TEXTAREA_WITH_ID_AND_DATA = u"""
<textarea id="sample_id">
    sample_value
</textarea>"""
TEXTAREA_WITH_NAME_ID_AND_DATA = u"""
<textarea name="sample_name" id="sample_id">
    sample_value
</textarea>"""
TEXTAREA_WITH_NAME_EMPTY = u'<textarea name=""></textarea>'

# Input templates
INPUT_TEXT_WITH_NAME = u'<input name="foo1" type="text" value="bar">'
INPUT_TEXT_WITH_ID = u'<input id="foo2" type="text" value="bar">'
INPUT_FILE_WITH_NAME = u'<input name="foo3" type="file" value="bar">'
INPUT_SUBMIT_WITH_NAME = u'<input name="foo4" type="submit">'
INPUT_RADIO_WITH_NAME = u'<input name="foo5" type="radio" checked>'
INPUT_CHECKBOX_WITH_NAME = u'<input name="foo6" type="checkbox" checked="true">'
INPUT_HIDDEN = u'<input name="foo7" type="hidden" value="bar">'

# Select templates
SELECT_WITH_NAME = u"""
<select name="vehicle">
    <option value=""></option>
    <option value="car"/>
    <option value="plane"></option>
    <option value="bike"></option>
    </option>
</select>"""
SELECT_WITH_ID = u"""
<select id="vehicle">
    <option value="car"/>
    <option value="plane"></option>
    <option value="bike"></option>
</select>"""

# Anchor templates
A_LINK_RELATIVE = u'<a href="/index.php">XXX</a>'
A_LINK_ABSOLUTE = u'<a href="http://w3af.com/home.php">XXX</a>'
A_LINK_FRAGMENT = u'<a href="#mark">XXX</a>'

# Other templates
BASE_TAG = u"""
<base href="http://www.w3afbase.com">
<base target="_blank">
"""
META_REFRESH = u"""<meta http-equiv="refresh" content="600">"""
META_REFRESH_WITH_URL = u"""
<meta http-equiv="refresh" content="2;url=http://crawler.w3af.com/">"""


URL_INST = URL('http://w3af.com')


def _build_http_response(url, body_content, headers=Headers()):
    if 'content-type' not in headers:
        headers['content-type'] = 'text/html'
    return HTTPResponse(200, body_content, headers, url, url, charset='utf-8')

# We subclass SGMLParser to prevent that the parsing process
# while init'ing the parser instance


class _SGMLParser(SGMLParser):

    def __init__(self, http_resp):
        # Save "_parse" reference
        orig_parse = self._parse
        # Monkeypatch it!
        self._parse = lambda arg: None
        # Now call parent's __init__
        SGMLParser.__init__(self, http_resp)
        # Restore it
        self._parse = orig_parse


@attr('smoke')
class TestSGMLParser(unittest.TestCase):

    def test_get_emails_filter(self):
        resp = _build_http_response(URL_INST, '')
        p = _SGMLParser(resp)
        p._emails = {'a@w3af.com', 'foo@not.com'}

        self.assertEqual(p.get_emails(), {'a@w3af.com', 'foo@not.com'})

        self.assertEqual(p.get_emails(domain='w3af.com'), ['a@w3af.com'])
        self.assertEqual(p.get_emails(domain='not.com'), ['foo@not.com'])

    def test_extract_emails_blank(self):
        resp = _build_http_response(URL_INST, '')
        p = _SGMLParser(resp)

        self.assertEqual(p.get_emails(), set())

    def test_extract_emails_mailto(self):
        body = u'<a href="mailto:abc@w3af.com">test</a>'
        resp = _build_http_response(URL_INST, body)
        p = _SGMLParser(resp)
        p._parse(resp)

        expected_res = {u'abc@w3af.com'}
        self.assertEqual(p.get_emails(), expected_res)

    def test_extract_emails_mailto_dup(self):
        body = u'<a href="mailto:abc@w3af.com">a</a>'\
               u'<a href="mailto:abc@w3af.com">b</a>'
        resp = _build_http_response(URL_INST, body)
        p = _SGMLParser(resp)
        p._parse(resp)

        expected_res = {u'abc@w3af.com'}
        self.assertEqual(p.get_emails(), expected_res)

    def test_extract_emails_mailto_not_dup(self):
        body = u'<a href="mailto:abc@w3af.com">a</a>'\
               u'<a href="mailto:abc_def@w3af.com">b</a>'
        resp = _build_http_response(URL_INST, body)
        p = _SGMLParser(resp)
        p._parse(resp)

        expected_res = {u'abc@w3af.com', u'abc_def@w3af.com'}
        self.assertEqual(p.get_emails(), expected_res)

    def test_mailto_subject_body(self):
        body = u'<a href="mailto:abc@w3af.com?subject=testing out mailto'\
               u'&body=Just testing">test</a>'
        resp = _build_http_response(URL_INST, body)
        p = _SGMLParser(resp)
        p._parse(resp)

        expected_res = {u'abc@w3af.com'}
        self.assertEqual(p.get_emails(), expected_res)

    def test_parser_attrs(self):
        body_content = HTML_DOC % {'head': '', 'body': ''}
        p = _SGMLParser(_build_http_response(URL_INST, body_content))

        # Assert parser has these attrs correctly initialized
        self.assertFalse(getattr(p, '_inside_form'))
        self.assertFalse(getattr(p, '_inside_select'))
        self.assertFalse(getattr(p, '_inside_textarea'))
        self.assertFalse(getattr(p, '_inside_script'))

        self.assertEquals(set(), getattr(p, '_tag_and_url'))
        self.assertEquals(set(), getattr(p, '_parsed_urls'))
        self.assertEquals([], getattr(p, '_forms'))
        self.assertEquals([], getattr(p, '_comments_in_doc'))
        self.assertEquals([], getattr(p, '_meta_redirs'))
        self.assertEquals([], getattr(p, '_meta_tags'))

    def test_baseurl(self):
        body = HTML_DOC % {'head': BASE_TAG, 'body': ''}
        resp = _build_http_response(URL_INST, body)
        p = _SGMLParser(resp)
        p._parse(resp)
        self.assertEquals(URL('http://www.w3afbase.com/'), p._base_url)

    def test_meta_tags(self):
        body = HTML_DOC % \
            {'head': META_REFRESH + META_REFRESH_WITH_URL,
             'body': ''}
        resp = _build_http_response(URL_INST, body)
        p = _SGMLParser(resp)
        p._parse(resp)
        self.assertTrue(2, len(p.meta_redirs))
        self.assertTrue("2;url=http://crawler.w3af.com/" in p.meta_redirs)
        self.assertTrue("600" in p.meta_redirs)
        self.assertEquals([URL('http://crawler.w3af.com/')], p.references[0])

    def test_case_sensitivity(self):
        """
        Ensure handler methods are *always* called with lowered-cased
        tag and attribute names
        """
        def islower(s):
            il = False
            if isinstance(s, basestring):
                il = s.islower()
            else:
                il = all(k.islower() for k in s)
            assert il, "'%s' is not lowered-case" % s
            return il

        def start_wrapper(orig_start, tag, attrs):
            islower(tag)
            islower(attrs)
            return orig_start(tag, attrs)

        tags = (A_LINK_ABSOLUTE, INPUT_CHECKBOX_WITH_NAME, SELECT_WITH_NAME,
                TEXTAREA_WITH_ID_AND_DATA, INPUT_HIDDEN)
        ops = "lower", "upper", "title"

        for indexes in combinations(range(len(tags)), 2):

            body_elems = []

            for index, tag in enumerate(tags):
                ele = tag
                if index in indexes:
                    ele = getattr(tag, choice(ops))()
                body_elems.append(ele)

            body = HTML_DOC % {'head': '', 'body': ''.join(body_elems)}
            resp = _build_http_response(URL_INST, body)
            p = _SGMLParser(resp)
            orig_start = p.start
            wrapped_start = partial(start_wrapper, orig_start)
            p.start = wrapped_start
            p._parse(resp)

    def test_parsed_references(self):
        # The *parsed* urls *must* come both from valid tags and tag attributes
        # Also invalid urls like must be ignored (like javascript instructions)
        body = """
        <html>
            <a href="/x.py?a=1" Invalid_Attr="/invalid_url.php">
            <form action="javascript:history.back(1)">
                <tagX href="/py.py"/>
            </form>
        </html>"""
        r = _build_http_response(URL_INST, body)
        p = _SGMLParser(r)
        p._parse(r)
        parsed_refs = p.references[0]
        self.assertEquals(1, len(parsed_refs))
        self.assertEquals(
            'http://w3af.com/x.py?a=1', parsed_refs[0].url_string)

    def test_reference_with_colon(self):
        body = """
        <html>
            <a href="d:url.html?id=13&subid=3">foo</a>
        </html>"""
        r = _build_http_response(URL_INST, body)
        p = _SGMLParser(r)
        p._parse(r)
        parsed_refs = p.references[0]
        #
        #    Finding zero URLs is the correct behavior based on what
        #    I've seen in Opera and Chrome.
        #
        self.assertEquals(0, len(parsed_refs))

    def test_eval_xpath_in_dom(self):
        html = """
        <html>
          <head>
            <title>THE TITLE</title>
          </head>
          <body>
            <input name="user" type="text">
            <input name="pass" type="password">
          </body>
        </html>"""
        headers = Headers([('Content-Type', 'text/xml')])
        r = _build_http_response(URL_INST, html, headers)

        p = _SGMLParser(r)
        p._parse(r)

        self.assertEquals(2, len(p.get_dom().xpath('.//input')))

    def test_get_clear_text_body(self):
        html = 'header <b>ABC</b>-<b>DEF</b>-<b>XYZ</b> footer'
        clear_text = 'header ABC-DEF-XYZ footer'
        headers = Headers([('Content-Type', 'text/html')])
        r = _build_http_response(URL_INST, html, headers)

        p = _SGMLParser(r)
        p._parse(r)

        self.assertEquals(clear_text, p.get_clear_text_body())

    def test_get_clear_text_body_memoized(self):
        html = 'header <b>ABC</b>-<b>DEF</b>-<b>XYZ</b> footer'
        clear_text = 'header ABC-DEF-XYZ footer'
        headers = Headers([('Content-Type', 'text/html')])
        r = _build_http_response(URL_INST, html, headers)

        p = _SGMLParser(r)
        p._parse(r)

        calculated_clear_text = p.get_clear_text_body()
        calculated_clear_text_2 = p.get_clear_text_body()

        self.assertEquals(clear_text, calculated_clear_text)
        self.assertIs(calculated_clear_text_2, calculated_clear_text)

    def test_get_clear_text_body_encodings(self):

        raise SkipTest('Not sure why this one is failing :S')

        for lang_desc, (body, encoding) in TEST_RESPONSES.iteritems():
            encoding_header = 'text/html; charset=%s' % encoding
            headers = Headers([('Content-Type', encoding_header)])

            encoded_body = body.encode(encoding)
            r = _build_http_response(URL_INST, encoded_body, headers)

            p = _SGMLParser(r)
            p._parse(r)

            ct_body = p.get_clear_text_body()

            # These test strings don't really have tags, so they should be eq
            self.assertEqual(ct_body, body)

    def test_get_clear_text_issue_4402(self):
        """
        :see: https://github.com/andresriancho/w3af/issues/4402
        """
        test_file_path = 'core/data/url/tests/data/encoding_4402.php'
        test_file = os.path.join(ROOT_PATH, test_file_path)
        body = file(test_file, 'rb').read()

        sample_encodings = [encoding for _, (_, encoding) in TEST_RESPONSES.iteritems()]
        sample_encodings.extend(['', 'utf-8'])

        for encoding in sample_encodings:
            encoding_header = 'text/html; charset=%s' % encoding
            headers = Headers([('Content-Type', encoding_header)])

            r = _build_http_response(URL_INST, body, headers)

            p = _SGMLParser(r)
            p._parse(r)

            p.get_clear_text_body()

    def test_not_pickleable_dom(self):
        """
        Since we can't pickle when there is a dom, there are some things which
        I won't be able to do (just as sending the parser over the wire).

        This test is just a reminder of that fact.
        """
        html = 'header <b>ABC</b>-<b>DEF</b>-<b>XYZ</b> footer'
        headers = Headers([('Content-Type', 'text/html')])
        r = _build_http_response(URL_INST, html, headers)

        p = _SGMLParser(r)
        p._parse(r)

        # This just calculates the DOM and stores it as an attribute, NEEDS
        # to be done before pickling (dumps) to have a real test.
        p.get_dom()

        self.assertRaises(TypeError, cPickle.dumps, p)


# We subclass HTMLParser to prevent that the parsing process
# while init'ing the parser instance
class _HTMLParser(HTMLParser):

    def __init__(self, http_resp):
        # Save "_parse" reference
        orig_parse = self._parse
        # Monkeypatch it!
        self._parse = lambda arg: None
        # Now call parent's __init__
        HTMLParser.__init__(self, http_resp)
        # Restore it
        self._parse = orig_parse


@attr('smoke')
class TestHTMLParser(unittest.TestCase):

    def test_forms(self):
        body = HTML_DOC % \
            {'head': '',
             'body': FORM_METHOD_GET % {'form_content': ''} +
                     FORM_WITHOUT_ACTION % {'form_content': ''}
             }
        resp = _build_http_response(URL_INST, body)
        p = _HTMLParser(resp)
        p._parse(resp)
        self.assertEquals(2, len(p.forms))

    def test_no_forms(self):
        # No form should be parsed
        body = HTML_DOC % \
            {'head': '',
             'body': (INPUT_TEXT_WITH_NAME + INPUT_HIDDEN + SELECT_WITH_ID +
                      TEXTAREA_WITH_ID_AND_DATA + INPUT_FILE_WITH_NAME)
             }
        resp = _build_http_response(URL_INST, body)
        p = _HTMLParser(resp)
        p._parse(resp)
        self.assertEquals(0, len(p.forms))

    def test_form_without_method(self):
        """
        When the form has no 'method' => 'GET' will be used
        """
        body = HTML_DOC % \
            {'head': '',
                     'body': FORM_WITHOUT_METHOD % {'form_content': ''}
             }
        resp = _build_http_response(URL_INST, body)
        p = _HTMLParser(resp)
        p._parse(resp)
        self.assertEquals('GET', p.forms[0].get_method())

    def test_form_without_action(self):
        """
        If the form has no 'content' => HTTPResponse's url will be used
        """
        body = HTML_DOC % \
            {'head': '',
                     'body': FORM_WITHOUT_ACTION % {'form_content': ''}
             }
        resp = _build_http_response(URL_INST, body)
        p = _HTMLParser(resp)
        p._parse(resp)
        self.assertEquals(URL_INST, p.forms[0].get_action())

    def test_form_with_invalid_url_in_action(self):
        """
        If an invalid URL is detected in the form's action then use base_url
        """
        body = """
        <html>
            <form action="javascript:history.back(1)">
            </form>
        </html>"""
        r = _build_http_response(URL_INST, body)
        p = _HTMLParser(r)
        p._parse(r)
        self.assertEquals(URL_INST, p.forms[0].get_action())

    def test_form_multiline_tags(self):
        """
        Found this form on the wild and was unable to parse it.
        """
        resp = _build_http_response(URL_INST, FORM_MULTILINE_TAGS)
        p = _HTMLParser(resp)
        p._parse(resp)
        
        self.assertEqual(1, len(p.forms))
        form = p.forms[0]
        
        self.assertEquals(URL_INST, form.get_action())
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
        resp = _build_http_response(URL_INST, body)
        p = _HTMLParser(resp)
        p._parse(resp)

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
        resp2 = _build_http_response(URL_INST, body2)
        p2 = _HTMLParser(resp2)
        p2._parse(resp2)

        # Only one form
        self.assertTrue(len(p.forms) == 1)
        # Ensure that parsed inputs actually belongs to the form and
        # have the expected values
        f = p.forms[0]
        self.assertEquals(['bar'], f['foo1'])  # text input
        self.assertEquals(['bar'], f['foo2'])  # text input
        self.assertEquals([''], f['foo3'])  # file input
        self.assertEquals([''], f['foo5'])  # radio input
        self.assertEquals([''], f['foo6'])  # checkbox input
        self.assertEquals(['bar'], f['foo7'])  # hidden input
        self.assertEquals('', f._submit_map['foo4'])  # submit input

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
        resp = _build_http_response(URL_INST, body)
        p = _HTMLParser(resp)
        p._parse(resp)

        # textarea are parsed as regular inputs
        f = p.forms[0]
        self.assertTrue(f.get('sample_id') == f.get('sample_name') ==
                        ['sample_value'])
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
        resp = _build_http_response(URL_INST, body)
        p = _HTMLParser(resp)
        p._parse(resp)

        # No pending parsed selects
        self.assertEquals(0, len(p._selects))

        # Only 1 select (2 have the same name); the last one is not parsed as
        # it has no name/id
        f = p.forms[0]
        self.assertEquals(1, len(f._selects))
        vehicles = f._selects['vehicle']
        self.assertTrue(vehicles.count("car") == vehicles.count("plane") ==
                        vehicles.count("bike") == 2)

        # "xxx" and "yyy" options were not parsed
        self.assertFalse("xxx" in f._selects.values())
        self.assertFalse("yyy" in f._selects.values())

    def test_form_with_repeated_parameter_names(self):
        # Setup
        form = FORM_METHOD_POST % {'form_content':
                                   TEXTAREA_WITH_NAME_AND_DATA * 2}
        body = HTML_DOC % {'head': '',
                           'body': form}
        resp = _build_http_response(URL_INST, body)
        p = _HTMLParser(resp)

        # Run the parser
        p._parse(resp)

        # Asserts
        self.assertEquals(1, len(p.forms))
        form = p.forms[0]

        self.assertIsInstance(form, FormParameters)
        self.assertEqual(form['sample_name'], ['sample_value',
                                               'sample_value'])

    def test_a_link_absolute(self):
        headers = Headers([('content-type', 'text/html')])
        resp = _build_http_response(URL_INST, A_LINK_ABSOLUTE, headers=headers)
        p = _HTMLParser(resp)
        p._parse(resp)

        self.assertEquals([URL('http://w3af.com/home.php')], p.references[0])

    def test_script_tag_link_extraction(self):
        body = '''<script>window.location = "http://w3af.com/";</script>'''
        resp = _build_http_response(URL_INST, body)
        p = _HTMLParser(resp)
        p._parse(resp)

        self.assertEquals([URL('http://w3af.com/')], p.references[1])

    def test_script_tag_link_extraction_relative(self):
        body = '''<script>window.location = "/foo.php";</script>'''
        resp = _build_http_response(URL_INST, body)
        p = _HTMLParser(resp)
        p._parse(resp)

        self.assertEquals([URL('http://w3af.com/foo.php')], p.references[1])