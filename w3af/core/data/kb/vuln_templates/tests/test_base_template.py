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

from mock import Mock
from w3af.core.data.kb.vuln_templates.base_template import BaseTemplate


class BaseTemplateTest(unittest.TestCase):
    
    def test_basic(self):
        bt = BaseTemplate()
        
        options_list = bt.get_options()
        name = options_list['name']
        url = options_list['url']
        data = options_list['data']
        method = options_list['method']
        vulnerable_parameter = options_list['vulnerable_parameter']
        
        name.set_value('SQL injection')
        url.set_value('http://host.tld/foo.php')
        data.set_value('id=3')
        method.set_value('GET')
        vulnerable_parameter.set_value('id')

        bt.get_vulnerability_name = Mock(return_value='unittest')
        bt.set_options(options_list)
        
        one = bt.get_vuln_id()
        two = bt.get_vuln_id()
        
        self.assertEqual(one + 1, two)
