# -*- coding: UTF-8 -*-
'''
test_profile.py

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
from core.controllers.w3afCore import w3afCore
from core.controllers.w3afException import w3afException


class Test_w3afCore_profiles(unittest.TestCase):

    def setUp(self):
        pass
    
    def test_useProfile(self):
        w3af_core = w3afCore()
        w3af_core.profiles.useProfile('OWASP_TOP10')
        
        enabled_plugins = w3af_core.plugins.getAllEnabledPlugins()
        
        self.assertTrue( 'sqli' in enabled_plugins['audit'])
        self.assertTrue( 'creditCards' in enabled_plugins['grep'])
        self.assertTrue( 'privateIP' in enabled_plugins['grep'])
        self.assertTrue( 'dnsWildcard' in enabled_plugins['discovery'])
        
    def test_saveCurrentToNewProfile(self):
        w3af_core = w3afCore()
        w3af_core.profiles.useProfile('OWASP_TOP10')
        
        audit = w3af_core.plugins.getEnabledPlugins('audit')
        disabled_plugin = audit[-1]
        audit = audit[:-1]
        w3af_core.plugins.setPlugins(audit,'audit')
        enabled = w3af_core.plugins.getEnabledPlugins('audit')
        self.assertEquals(enabled, audit)
        self.assertTrue(disabled_plugin not in enabled)

        w3af_core.profiles.saveCurrentToNewProfile('unittest-OWASP_TOP10')
        
        # Get a new, clean instance of the core.
        w3af_core = w3afCore()
        audit = w3af_core.plugins.getEnabledPlugins('audit')
        self.assertEquals( audit, [])

        w3af_core.profiles.useProfile('unittest-OWASP_TOP10')
        enabled_plugins = w3af_core.plugins.getAllEnabledPlugins()
        
        self.assertTrue( disabled_plugin not in enabled_plugins['audit'])
        self.assertTrue( 'creditCards' in enabled_plugins['grep'])
        self.assertTrue( 'privateIP' in enabled_plugins['grep'])
        self.assertTrue( 'dnsWildcard' in enabled_plugins['discovery'])        
        
        w3af_core.profiles.removeProfile('unittest-OWASP_TOP10')

    def test_removeProfile(self):
        w3af_core = w3afCore()
        w3af_core.profiles.saveCurrentToNewProfile('unittest-remove')
        w3af_core.profiles.removeProfile('unittest-remove')
        
        self.assertRaises(w3afException, w3af_core.profiles.useProfile,'unittest-remove')
        
    def test_removeProfile_not_exists(self):
        w3af_core = w3afCore()
        self.assertRaises(w3afException, w3af_core.profiles.removeProfile,'not-exists')
        
        