# -*- encoding: utf-8 -*-
"""
test_contains_source_code.py

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
import os
import unittest

from w3af.core.controllers.misc.contains_source_code import contains_source_code
from w3af.core.controllers.misc.contains_source_code import PHP, PYTHON, RUBY, JAVA
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af import ROOT_PATH


class TestContainsSourceCode(unittest.TestCase):
    TEST_FILE = os.path.join(ROOT_PATH, 'core', 'controllers', 'misc', 'tests',
                             'data', 'code-detect-false-positive.jpg')

    def create_response(self, body, content_type=None):
        content_type = content_type if content_type is not None else 'text/html'
        headers = Headers([('Content-Type', content_type)])
        url = URL('http://www.w3af.org/')
        return HTTPResponse(200, body, headers, url, url)

    def test_php(self):
        source = self.create_response('foo <?php echo "a"; ?> bar')
        match, lang = contains_source_code(source)

        self.assertNotEqual(match, None)
        self.assertEqual(lang, {PHP})
    
    def test_no_code_case01(self):
        source = self.create_response('foo <?php echo "bar')
        match, lang = contains_source_code(source)
        
        self.assertEqual(match, None)
        self.assertEqual(lang, None)
    
    def test_no_code_case02(self):
        source = self.create_response('foo <?xml ?> "bar')
        match, lang = contains_source_code(source)
        
        self.assertEqual(match, None)
        self.assertEqual(lang, None)

    def test_no_code_case03(self):
        source = self.create_response('foo <?php xpacket ?> "bar')
        match, lang = contains_source_code(source)
        
        self.assertEqual(match, None)
        self.assertEqual(lang, None)

    def test_code_case04(self):
        source = self.create_response('foo <?php ypacket ?> "bar')
        match, lang = contains_source_code(source)
        
        self.assertNotEqual(match, None)
        self.assertEqual(lang, {PHP})

    def test_code_python(self):
        source = self.create_response('''
                 def foo(self):
                    pass
                 ''')
        match, lang = contains_source_code(source)

        self.assertNotEqual(match, None)
        self.assertEqual(lang, {PYTHON})

    def test_code_java(self):
        source = self.create_response('''
                 public class Person{
                    public void printPerson() {
                      System.out.println(name + ", " + this.getAge());
                    }
                 }
                 ''')
        match, lang = contains_source_code(source)

        self.assertNotEqual(match, None)
        self.assertEqual(lang, {JAVA})

    def test_code_ruby_01(self):
        source = self.create_response('''class Person < ActiveRecord::Base
                        validates :name, presence: true
                    end''')
        match, lang = contains_source_code(source)

        self.assertNotEqual(match, None)
        self.assertEqual(lang, {RUBY})

    def test_code_ruby_02(self):
        source = self.create_response('''class Person
                        def say_hi
                            puts 'hi'
                        end
                    end''')
        match, lang = contains_source_code(source)

        self.assertNotEqual(match, None)
        self.assertEqual(lang, {RUBY})

    def test_code_false_positive_ruby_01(self):
        source = self.create_response('var f=_.template("<div class="alert'
                                      ' alert-error <% if (title) { %>'
                                      ' alert-block <% } %>',
                                      content_type='application/javascript')
        match, lang = contains_source_code(source)
        self.assertEqual(match, None)

    def test_code_false_positive_ruby_02(self):
        source = self.create_response('class IPs on VPS or Dedicated Server'
                                      ' <a href="/seo-hosting/">def</a>'
                                      ' ga("send',
                                      content_type='application/javascript')
        match, lang = contains_source_code(source)
        self.assertEqual(match, None)

    def test_code_false_positive_ruby_03(self):
        source = self.create_response('class IPs on VPS or Dedicated Server'
                                      ' <a href="/seo-hosting/"> def </a>'
                                      ' ga("send',
                                      content_type='application/javascript')
        match, lang = contains_source_code(source)
        self.assertEqual(match, None)

    def test_code_false_positive_ruby_04(self):
        """
        Will not match because of the </a> before end. End requires a space (\s)
        before the token.
        """
        source = self.create_response('class IPs on VPS or Dedicated Server'
                                      ' <a href="/seo-hosting/"> def </a>end',
                                      content_type='application/javascript')
        match, lang = contains_source_code(source)
        self.assertEqual(match, None)

    def test_code_false_positive_java_01(self):
        """
        Java source code regex matches bootstrap.js
        """
        source = self.create_response("""PUBLIC CLASS DEFINITION
                                      // ==============================

                                      var Button = function (element, options) {
                                        this.$element  = $(element)
                                        this.options   = $.extend({}, Button.DEFAULTS, options)
                                        this.isLoading = false
                                      }
                                      """,
                                      content_type='application/javascript')
        match, lang = contains_source_code(source)
        self.assertEqual(match, None)

    def test_code_false_positive_java_02(self):
        source = self.create_response('''
                 public class Person{
                 }
                 ''')
        match, lang = contains_source_code(source)
        self.assertEqual(match, None)

    def test_code_false_positive_image(self):
        no_source = self.create_response(file(self.TEST_FILE).read(),
                                         content_type='image/jpeg')
        match, lang = contains_source_code(no_source)
        self.assertEqual(match, None)

