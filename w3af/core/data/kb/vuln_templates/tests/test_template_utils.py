"""
test_utils.py

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

from w3af.core.data.kb.vuln_templates.utils import (get_all_templates,
                                                    get_template_names,
                                                    get_template_by_name)


class TestUtils(unittest.TestCase):
    
    def test_get_all_templates(self):
        templates = get_all_templates()
        template_names = [t.get_short_name() for t in templates]
        
        self.assertIn('dav', template_names)
    
    def test_get_template_names(self):
        self.assertIn('dav', get_template_names())
    
    def test_get_template_by_name(self):
        template = get_template_by_name('dav')
        self.assertEqual(template.get_short_name(), 'dav')
    
    def test_get_template_by_name_fail(self):
        self.assertRaises(Exception, get_template_by_name, 'foobar')
        