# -*- coding: utf8 -*-
"""
test_output_manager.py

Copyright 2011 Andres Riancho

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
import multiprocessing

from mock import MagicMock, Mock
from nose.plugins.attrib import attr
from tblib.decorators import Error

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.controllers.output_manager import log_sink_factory
from w3af.core.controllers.threads.decorators import apply_with_return_error


def send_log_message(msg):
    om.out.information(msg)


@attr('smoke')
class TestOutputManager(unittest.TestCase):

    OUTPUT_PLUGIN_ACTIONS = ('debug', 'information', 'error',
                             'console', 'vulnerability')

    def test_output_plugins_actions(self):
        """Call all actions on output plugins"""

        msg = '<< SOME OUTPUT MESS@GE!! <<'

        for action in TestOutputManager.OUTPUT_PLUGIN_ACTIONS:
            plugin = Mock()
            plugin_action = MagicMock()
            setattr(plugin, action, plugin_action)

            # Invoke action
            om.manager._output_plugin_instances = [plugin, ]
            om_action = getattr(om.out, action)
            om_action(msg, True)

            om.manager.process_all_messages()

            plugin_action.assert_called_once_with(msg, True)

    def test_output_plugins_actions_with_unicode_message(self):
        """Call all actions on output plugins using a unicode message"""
        msg = u'<< ÑñçÇyruZZ!! <<'
        utf8_encoded_msg = msg.encode('utf8')

        for action in TestOutputManager.OUTPUT_PLUGIN_ACTIONS:
            plugin = Mock()
            plugin_action = MagicMock()
            setattr(plugin, action, plugin_action)

            # Invoke action
            om.manager._output_plugin_instances = [plugin, ]
            om_action = getattr(om.out, action)
            om_action(msg, True)

            om.manager.process_all_messages()

            plugin_action.assert_called_once_with(utf8_encoded_msg, True)

    def test_method_that_not_exists(self):
        """The output manager implements __getattr__ and we don't want it to
        catch-all, just the ones I define!"""
        try:
            self.assertRaises(AttributeError, om.out.foobar, ('abc',))
        except AttributeError, ae:
            self.assertTrue(True, ae)

    def test_kwds(self):
        """The output manager implements __getattr__ with some added
        functools.partial magic. This verifies that it works well with kwds"""
        msg = 'foo bar spam eggs'
        action = 'information'

        plugin = Mock()
        plugin_action = MagicMock()
        setattr(plugin, action, plugin_action)

        # Invoke action
        om.manager._output_plugin_instances = [plugin, ]
        om_action = getattr(om.out, action)
        om_action(msg, False)

        om.manager.process_all_messages()

        plugin_action.assert_called_once_with(msg, False)
    
    def test_ignore_plugins(self):
        """The output manager implements ignore_plugins to avoid sending a
        message to a specific plugin. Test this feature."""
        msg = 'foo bar spam eggs'
        action = 'information'

        plugin = Mock()
        plugin_action = MagicMock()
        plugin_get_name = MagicMock(return_value='fake')
        setattr(plugin, action, plugin_action)
        setattr(plugin, 'get_name', plugin_get_name)

        # Invoke action
        om.manager._output_plugin_instances = [plugin, ]
        om_action = getattr(om.out, action)
        # This one will be ignored at the output manager level
        om_action(msg, False, ignore_plugins=set(['fake']))
        # This one will make it and we'll assert it below
        om_action(msg, False)
        
        om.manager.process_all_messages()

        plugin_action.assert_called_once_with(msg, False)        

    def test_error_handling(self):
        
        class InvalidPlugin(object):
            def flush(self):
                pass
            
            def information(self, msg, new_line=True):
                raise Exception('Test')

            def debug(self, *args, **kwargs):
                pass

            def error(self, msg, new_line=True):
                pass

            def get_name(self):
                return 'InvalidPlugin'

        invalid_plugin = InvalidPlugin()

        w3af_core = w3afCore()

        om.manager._output_plugin_instances = [invalid_plugin, ]
        om.manager.start()
        om.out.information('abc')
        om.manager.process_all_messages()

        exc_list = w3af_core.exception_handler.get_all_exceptions()
        self.assertEqual(len(exc_list), 1, exc_list)

        edata = exc_list[0]
        self.assertEqual(str(edata.exception), 'Test')

    def test_output_manager_multiprocessing(self):
        msg = 'Sent from a different process'

        action = 'information'

        plugin = Mock()
        plugin_action = MagicMock()
        setattr(plugin, action, plugin_action)
        om.manager._output_plugin_instances = [plugin, ]

        log_queue = om.manager.get_in_queue()
        _pool = multiprocessing.Pool(1,
                                     initializer=log_sink_factory,
                                     initargs=(log_queue,))

        result = _pool.apply(apply_with_return_error, ((send_log_message, msg),))
        if isinstance(result, Error):
            result.reraise()

        om.manager.process_all_messages()

        plugin_action.assert_called_once_with(msg)
