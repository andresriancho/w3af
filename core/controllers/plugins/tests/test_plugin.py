'''
test_plugin.py

Copyright 2006 Andres Riancho

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

from core.controllers.plugins.plugin import Plugin
from core.data.kb.vuln import Vuln
from core.data.parsers.url import URL

import core.data.constants.severity as severity


class TestPlugin(unittest.TestCase):
    
    def test_print_uniq_url(self):
        p = Plugin()
        
        v1 = Vuln('TestCase', 'description', severity.HIGH, 1, 'name')
        v1.set_url(URL('http://host.tld/'))
        
        v2 = Vuln('TestCase', 'description', severity.HIGH, 1, 'name')
        v2.set_url(URL('http://host.tld/'))
        
        info_obj = [v1, v2]
        
        informed = p.print_uniq(info_obj, 'URL')
        self.assertEqual(len(informed), 1)
        
    def test_print_uniq_var_case01(self):
        p = Plugin()
        
        v1 = Vuln('TestCase', 'description', severity.HIGH, 1, 'name')
        v1.set_url(URL('http://host.tld/'))
        v1.set_var('id')
        
        v2 = Vuln('TestCase', 'description', severity.HIGH, 1, 'name')
        v2.set_url(URL('http://host.tld/'))
        v2.set_var('id')
        
        info_obj = [v1, v2]
        
        informed = p.print_uniq(info_obj, 'VAR')
        self.assertEqual(len(informed), 1)

    def test_print_uniq_var_case02(self):
        p = Plugin()
        
        v1 = Vuln('TestCase', 'description', severity.HIGH, 1, 'name')
        v1.set_url(URL('http://host.tld/'))
        v1.set_var('id')
        
        v2 = Vuln('TestCase', 'description', severity.HIGH, 1, 'name')
        v2.set_url(URL('http://host.tld/'))
        v2.set_var('file')
        
        info_obj = [v1, v2]
        
        informed = p.print_uniq(info_obj, 'VAR')
        self.assertEqual(len(informed), 2)

    def test_print_uniq_none(self):
        p = Plugin()
        
        v1 = Vuln('TestCase', 'description', severity.HIGH, 1, 'name')
        v1.set_url(URL('http://host.tld/'))
        
        v2 = Vuln('TestCase', 'description', severity.HIGH, 1, 'name')
        v2.set_url(URL('http://host.tld/'))
        
        info_obj = [v1, v2]
        
        informed = p.print_uniq(info_obj, None)
        self.assertEqual(len(informed), 2)
