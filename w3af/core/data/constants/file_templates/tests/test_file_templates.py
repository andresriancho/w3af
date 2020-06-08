"""
test_file_templates.py

Copyright 2006 Andres Riancho

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

from w3af.core.data.constants.file_templates.file_templates import get_file_from_template


class TestFileTemplates(unittest.TestCase):
    def test_get_file_from_template_true(self):
        success, file_content, file_name = get_file_from_template('gif')

        self.assertTrue(success)
        self.assertIn('GIF', file_content)
        self.assertTrue(file_name.endswith('.gif'), file_name)

    def test_get_file_from_template_false(self):
        success, file_content, file_name = get_file_from_template('swf')

        self.assertFalse(success)
        self.assertTrue(file_name.endswith('.swf'), file_name)
