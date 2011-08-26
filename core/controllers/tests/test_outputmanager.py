# -*- coding: utf8 -*-
'''
test_outputmanager.py

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

import inspect

from pymock import PyMockTestCase, method

from ..outputManager import outputManager


class TestOutputManager(PyMockTestCase):
    
    OUTPUT_PLUGIN_ACTIONS = ('debug', 'information', 'error',
                             'console', 'vulnerability')

    def setUp(self):
        PyMockTestCase.setUp(self)
        self.om = outputManager()

    def test_output_plugins_actions(self):
        '''Call all actions on output plugins'''
        
        msg = '<< SOME OUTPUT MESS@GE!! <<'
        
        for action in TestOutputManager.OUTPUT_PLUGIN_ACTIONS:
            plugin = self.mock()
            self.om._outputPluginList = [plugin]
            pluginaction = getattr(self.om, action)
            defvals = inspect.getargspec(pluginaction)[3]
            method(plugin, action).expects(msg, *defvals) 
            
            ## Stop recording. Play!
            self.replay()
            
            # Invoke action
            pluginaction(msg, True)
            
            # Verify and reset
            self.verify()
            self.reset()
    
    
    def test_output_plugins_actions_with_unicode_message(self):
        '''Call all actions on output plugins using a unicode message'''
        
        msg = u'<< ÑñçÇyruZZ!! <<'
        utf8_encoded_msg = msg.encode('utf8')
        
        for action in TestOutputManager.OUTPUT_PLUGIN_ACTIONS:
            plugin = self.mock()
            self.om._outputPluginList = [plugin]
            pluginaction = getattr(self.om, action)
            actiondefvals = inspect.getargspec(pluginaction)[3]
            method(plugin, action).expects(utf8_encoded_msg, *actiondefvals) 
            
            ## Stop recording. Play!
            self.replay()
            
            # Invoke action
            pluginaction(msg, True)
            
            # Verify and reset
            self.verify()
            self.reset()
    