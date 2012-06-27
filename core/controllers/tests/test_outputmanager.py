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

from pymock import PyMockTestCase, method

from core.controllers.coreHelpers.exception_handler import exception_handler
import core.controllers.outputManager as om


class TestOutputManager(PyMockTestCase):
    
    OUTPUT_PLUGIN_ACTIONS = ('debug', 'information', 'error',
                             'console', 'vulnerability')

    def setUp(self):
        PyMockTestCase.setUp(self)
        om.start_output_manager()

    def test_output_plugins_actions(self):
        '''Call all actions on output plugins'''
        
        msg = '<< SOME OUTPUT MESS@GE!! <<'
        
        for action in TestOutputManager.OUTPUT_PLUGIN_ACTIONS:
            plugin = self.mock()
            om.out._output_plugin_list = [plugin,]
            om_action = getattr(om.out, action)
            method(plugin, action).expects(msg, True) 
            
            ## Stop recording. Play!
            self.replay()
            
            # Invoke action
            om_action(msg, True)
            om.out.process_all_messages()
            
            # Verify and reset
            self.verify()
            self.reset()
    
    def test_output_plugins_actions_with_unicode_message(self):
        '''Call all actions on output plugins using a unicode message'''
        
        msg = u'<< ÑñçÇyruZZ!! <<'
        utf8_encoded_msg = msg.encode('utf8')

        for action in TestOutputManager.OUTPUT_PLUGIN_ACTIONS:
            plugin = self.mock()
            om.out._output_plugin_list = [plugin,]
            om_action = getattr(om.out, action)
            method(plugin, action).expects(utf8_encoded_msg, True) 
            
            ## Stop recording. Play!
            self.replay()
            
            # Invoke action
            om_action(msg, True)
            om.out.process_all_messages()
            
            # Verify and reset
            self.verify()
            self.reset()        
    
    def test_method_that_not_exists(self):
        '''The output manager implements __getattr__ and we don't want it to
        catch-all, just the ones I define!'''
        try:
            self.assertRaises(AttributeError, om.out.foobar, ('abc',))
        except AttributeError:
            pass

    def test_kwds(self):
        '''The output manager implements __getattr__ with some added
        functools.partial magic. This verifies that it works well with kwds'''
        
        msg = 'foo bar spam eggs'
        action = 'information'
        
        plugin = self.mock()
        om.out._output_plugin_list = [plugin,]
        om_action = getattr(om.out, action)
        method(plugin, action).expects(msg, newLine=False) 
        
        ## Stop recording. Play!
        self.replay()
        
        # Invoke action
        om_action(msg, newLine=False)
        om.out.process_all_messages()
        
        # Verify and reset
        self.verify()
        self.reset()
    
    def test_error_handling(self):
        
        class InvalidPlugin(object):
            def information(self, msg, newLine=True):
                raise Exception('Test')
            
            def error(self, msg, newLine=True):
                pass
            
            def getName(self):
                return 'InvalidPlugin'
        
        invalid_plugin = InvalidPlugin() 
        
        om.out._output_plugin_list = [invalid_plugin,]
        om.out.information('abc')
        om.out.process_all_messages()
        
        exc_list = exception_handler.get_all_exceptions()
        self.assertEqual(len(exc_list), 1, exc_list)
        
        edata = exc_list[0]
        self.assertEqual( str(edata.exception) , 'Test' )
        
        self.reset()
        