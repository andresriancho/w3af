# -*- coding: UTF-8 -*-
'''
test_sgmlparsers.py

Copyright 2011 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
from pymock import PyMockTestCase, IfTrue, override, at_least

from ..htmlParser import HTMLParser
from ..sgmlParser import SGMLParser
from core.data.parsers.urlParser import url_object
from core.data.url.httpResponse import httpResponse

HTML_DOC = u'''
<html>
    <head>
        %(head)s
    </head>
    <body>
        %(body)s
    </body>
</html>
'''

# Form templates
FORM_METHOD_GET = u'''
<form method="GET" action="/index.php">
    %(form_content)s
</form>
'''
FORM_METHOD_POST = u'''
<form method="POST" action="/index.php">
    %(form_content)s
</form>
'''
FORM_WITHOUT_METHOD = u'''
<form action="/index.php">
    %(form_content)s
</form>
'''
FORM_WITHOUT_ACTION = u'''
<form method="POST">
    %(form_content)s
</form>
'''

# Textarea templates
TEXTAREA_WITH_NAME_AND_DATA = u'''
<textarea name="sample_name">
    sample_value
</textarea>'''
TEXTAREA_WITH_ID_AND_DATA = u'''
<textarea id="sample_id">
    sample_value
</textarea>'''
TEXTAREA_WITH_NAME_ID_AND_DATA = u'''
<textarea name="sample_name" id="sample_id">
    sample_value
</textarea>'''
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
SELECT_WITH_NAME = u'''
<select name="vehicle">
    <option value=""></option>
    <option value="car"/>
    <option value="plane"></option>
    <option value="bike"></option>
    </option>
</select>'''
SELECT_WITH_ID = u'''
<select id="vehicle">
    <option value="car"/>
    <option value="plane"></option>
    <option value="bike"></option>
</select>'''

# Anchor templates
A_LINK_RELATIVE = u'<a href="/index.php">XXX</a>'
A_LINK_ABSOLUTE = u'<a href="www.w3af.com/home.php">XXX</a>'
A_LINK_FRAGMENT = u'<a href="#mark">XXX</a>'

# Other templates
BASE_TAG = u'''
<base href="http://www.w3afbase.com">
<base target="_blank">
'''
META_REFRESH = u'''<meta http-equiv="refresh" content="600">'''
META_REFRESH_WITH_URL = u'''
<meta http-equiv="refresh" content="2;url=http://crawler.w3af.com/">'''
BODY_FRAGMENT_WITH_EMAILS = u'''===>jandalia@bing.com%^&1!
<script>ariancho%40gmail.com<script> name_with_ñ@w3af.it
תגובות_לאתר
'''

URL = url_object('http://w3af.com')

def _build_http_response(url, body_content, headers={}):
    if 'content-type' not in headers:
        headers['content-type'] = 'text/html'
    return httpResponse(200, body_content, headers, url, url, charset='utf-8')

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
        

class TestSGMLParser(PyMockTestCase):

    def setUp(self):
        PyMockTestCase.setUp(self)
    
    def test_parser_attrs(self):
        body_content = HTML_DOC % {'head':'', 'body':''}
        p = _SGMLParser(_build_http_response(URL, body_content))
        
        # Assert parser has these attrs correctly initialized
        self.assertFalse(getattr(p, '_inside_form'))
        self.assertFalse(getattr(p, '_inside_select'))
        self.assertFalse(getattr(p, '_inside_textarea'))
        self.assertFalse(getattr(p, '_inside_script'))
        
        self.assertEquals(set(), getattr(p, '_tag_and_url'))
        self.assertEquals(set(), getattr(p, '_parsed_urls'))
        self.assertEquals([], getattr(p, '_forms'))
        self.assertEquals([], getattr(p, '_comments_in_doc'))
        self.assertEquals([], getattr(p, '_scripts_in_doc'))
        self.assertEquals([], getattr(p, '_meta_redirs'))
        self.assertEquals([], getattr(p, '_meta_tags'))

    def test_baseurl(self):
        body = HTML_DOC % {'head': BASE_TAG, 'body': ''}
        resp = _build_http_response(URL, body)
        p = _SGMLParser(resp)
        p._parse(resp)
        self.assertEquals(url_object('http://www.w3afbase.com/'), p._baseUrl)
        
    def test_regex_urls(self):
        u1 = u'http://w3af.com/tréasure.php?id=ÓRÓª'
        u2 = u'http://w3af.com/tésoro.php?id=GÓLD'
        u3 = u'http://w3af.com/gold.py?típo=silvër'
        body = '''
        <html>
          <body>estas s%C3%B3n las urls absolutas q te comente para llegar al tesoro<br>
                http://w3af.com/t%C3%A9soro.php?id=G%C3%93LD http://w3af.com/tr%C3%A9asure.php?id=%C3%93R%C3%93%C2%AA
            y las relativas son<br>
                /gold.py?t%C3%ADpo=silv%C3%ABr
        '''
        resp = _build_http_response(URL, body)
        p = _SGMLParser(resp)
        urls = tuple(u.url_string for u in p._re_urls)
        self.assertTrue(u1 in urls)
        self.assertTrue(u2 in urls)
        self.assertTrue(u3 in urls)
    
    def test_meta_tags(self):
        body = HTML_DOC % \
            {'head': META_REFRESH + META_REFRESH_WITH_URL,
            'body': ''}
        resp = _build_http_response(URL, body)
        p = _SGMLParser(resp)
        p._parse(resp)
        self.assertTrue(2, len(p.meta_redirs))
        self.assertTrue("2;url=http://crawler.w3af.com/" in p.meta_redirs)
        self.assertTrue("600" in p.meta_redirs)
        self.assertEquals([url_object('http://crawler.w3af.com/')], p.references[0])
    
    def test_case_sensitivity(self):
        '''
        Ensure handler methods are *always* called with lowered-cased
        tag and attribute names
        '''
        def islower(s):
            il = False
            if isinstance(s, basestring):
                il = s.islower()
            elif isinstance(s, dict):
                il = all(k.islower() for k in s)
            assert il, "'%s' is not lowered-case" % s 
            return il
        
        from itertools import combinations
        from random import choice
        
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
            resp = _build_http_response(URL, body)
            p = _SGMLParser(resp)
            args = (IfTrue(islower), IfTrue(islower))
            override(p, 'start').expects(*args).returns(None).at_least(10)
            # Replay
            self.replay()
            p._parse(resp)
            # Verify and reset
            self.verify()
            self.reset()
            
    
    def test_find_emails(self):
        body = HTML_DOC % {'head': '', 'body': BODY_FRAGMENT_WITH_EMAILS}
        p = _SGMLParser(_build_http_response(URL, body))
        emails = ['jandalia@bing.com', 'ariancho@gmail.com',
                  u'name_with_ñ@w3af.it']
        self.assertEquals(emails, p.getEmails())

    def test_parsed_references(self):
        # The *parsed* urls *must* come both from valid tags and tag attributes
        # Also invalid urls like must be ignored (like javascript instructions)
        body = '''
        <html>
            <a href="/x.py?a=1" Invalid_Attr="/invalid_url.php">
            <form action="javascript:history.back(1)">
                <tagX href="/py.py"/>
            </form>
        </html>'''
        r = _build_http_response(URL, body)
        p = _SGMLParser(r)
        p._parse(r)
        parsed_refs = p.references[0]
        self.assertEquals(1, len(parsed_refs))
        self.assertEquals('http://w3af.com/x.py?a=1', parsed_refs[0].url_string)
    
    def test_reference_with_colon(self):
        body = '''
        <html>
            <a href="d:url.html?id=13&subid=3">foo</a>
        </html>'''
        r = _build_http_response(URL, body)
        p = _SGMLParser(r)
        p._parse(r)
        parsed_refs = p.references[0]
        #
        #    Finding zero URLs is the correct behavior based on what
        #    I've seen in Opera and Chrome.
        #
        self.assertEquals(0, len(parsed_refs))         
        

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


class TestHTMLParser(PyMockTestCase):

    def setUp(self):
        PyMockTestCase.setUp(self)

    def test_forms(self):
        body = HTML_DOC % \
            {'head': '',
             'body': FORM_METHOD_GET % {'form_content': ''} +
                     FORM_WITHOUT_ACTION % {'form_content': ''}
            }
        resp = _build_http_response(URL, body)
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
        resp = _build_http_response(URL, body)
        p = _HTMLParser(resp)
        p._parse(resp)
        self.assertEquals(0, len(p.forms))
    
    def test_form_without_meth(self):
        '''
        When the form has no 'method' => 'GET' will be used 
        '''
        body = HTML_DOC % \
                    {'head': '',
                     'body': FORM_WITHOUT_METHOD % {'form_content': ''}
                    }
        resp = _build_http_response(URL, body)
        p = _HTMLParser(resp)
        p._parse(resp)
        self.assertEquals('GET', p.forms[0].getMethod())
    
    def test_form_without_action(self):
        '''
        If the form has no 'content' => httpResponse's url will be used
        '''
        body = HTML_DOC % \
                    {'head': '',
                     'body': FORM_WITHOUT_ACTION % {'form_content': ''}
                    }
        resp = _build_http_response(URL, body)
        p = _HTMLParser(resp)
        p._parse(resp)
        self.assertEquals(URL, p.forms[0].getAction())
    
    def test_form_with_invalid_url_in_action(self):
        '''
        If an invalid url is detected in the form's action then use baseUrl
        '''
        body = '''
        <html>
            <form action="javascript:history.back(1)">
            </form>
        </html>'''
        r = _build_http_response(URL, body)
        p = _HTMLParser(r)
        p._parse(r)
        self.assertEquals(URL, p.forms[0].getAction())
    
    def test_inputs_in_out_form(self):
        # We expect that the form contains all the inputs (both those declared
        # before and after). Also it must be equal to a form that includes 
        # those same inputs but declared before them
        
        # 1st body
        body = HTML_DOC % \
            {'head': '',
             'body': (INPUT_TEXT_WITH_NAME + INPUT_TEXT_WITH_ID +
                  INPUT_FILE_WITH_NAME + INPUT_SUBMIT_WITH_NAME +
                  (FORM_WITHOUT_METHOD % {'form_content': ''}) + # form in the middle
                  INPUT_RADIO_WITH_NAME + INPUT_CHECKBOX_WITH_NAME +
                  INPUT_HIDDEN)
            }
        resp = _build_http_response(URL, body)
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
        resp2 = _build_http_response(URL, body2)
        p2 = _HTMLParser(resp2)
        p2._parse(resp2)
        
        # Only one form
        self.assertTrue(len(p.forms) == 1)
        # Ensure that parsed inputs actually belongs to the form and
        # have the expected values
        f = p.forms[0]
        self.assertEquals(['bar'], f['foo1']) # text input
        self.assertEquals(['bar'], f['foo2']) # text input
        self.assertEquals([''], f['foo3']) # file input
        self.assertEquals([''], f['foo5']) # radio input
        self.assertEquals([''], f['foo6']) # checkbox input
        self.assertEquals(['bar'], f['foo7']) # hidden input
        self.assertEquals('', f._submitMap['foo4']) # submit input
        
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
        resp = _build_http_response(URL, body)
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
        resp = _build_http_response(URL, body)
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
        
        