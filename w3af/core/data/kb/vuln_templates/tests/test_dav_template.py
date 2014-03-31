"""
test_base_template.py

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

from w3af.core.data.kb.vuln_templates.dav_template import DAVTemplate
from w3af.core.data.kb.knowledge_base import kb


class DAVTemplateTest(unittest.TestCase):
    def test_store_in_kb(self):
        dt = DAVTemplate()
        dt.store_in_kb()
        
        stored_data = kb.get(*dt.get_kb_location())
        
        self.assertEqual(len(stored_data), 1)
        
        stored_vuln = stored_data[0]
        created_vuln = dt.create_vuln()
        
        stored_vuln.set_id(created_vuln.get_id())
        
        self.assertEqual(stored_vuln, created_vuln)
        
        