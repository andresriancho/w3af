'''
test_update_URLs_in_KB.py

Copyright 2012 Andres Riancho

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
import unittest

import core.data.kb.knowledgeBase as kb

from core.data.parsers.urlParser import url_object
from core.data.request.fuzzable_request import fuzzable_request
from core.controllers.core_helpers.update_urls_in_kb import update_kb


class TestUpdateURLs(unittest.TestCase):
    
    def setUp(self):
        kb.kb.save('urls', 'url_objects', list())
        kb.kb.save('urls', 'fuzzable_requests', set())
    
    def test_basic(self):
        u1 = url_object('http://w3af.org/')
        r1 = fuzzable_request(u1, method='GET')
        update_kb( r1 )
        result = kb.kb.getData('urls', 'url_objects')
        self.assertEquals(len(result), 1)
        self.assertEquals("http://w3af.org/", list(result)[0].url_string)
        
        u2 = url_object('http://w3af.org/blog/')
        r2 = fuzzable_request(u2, method='GET')    
        u3 = url_object('http://w3af.org/')
        r3 = fuzzable_request(u3, method='GET')    
        update_kb( r1 )
        update_kb( r2 )
        update_kb( r3 )
        
        result = kb.kb.getData('urls', 'url_objects')
        self.assertEquals(len(result), 2)
        expected_set = set(["http://w3af.org/", "http://w3af.org/blog/"])
        self.assertEqual( expected_set,
                          set([u.url_string for u in result]))
        
    