"""
test_core_exceptions.py

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

from mock import patch, call
from nose.plugins.attrib import attr

from w3af.core.data.parsers.doc.url import URL
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.controllers.misc.factory import factory
from w3af.core.controllers.exceptions import (ScanMustStopException,
                                              ScanMustStopByUnknownReasonExc,
                                              ScanMustStopByUserRequest)
from w3af.plugins.tests.helper import create_target_option_list


@attr('moth')
class TestCoreExceptions(unittest.TestCase):
    """
    TODO: Think about mocking all calls to ExtendedUrllib in order to avoid
          being tagged as 'moth'.
    """
    PLUGIN = 'w3af.core.controllers.tests.exception_raise'
    
    def setUp(self):
        """
        This is a rather complex setUp since I need to move the
        exception_raise.py plugin to the plugin directory in order to be able
        to run it afterwards.

        In the tearDown method, I'll remove the file.
        """
        self.w3afcore = w3afCore()
        
        target_opts = create_target_option_list(URL(get_moth_http()))
        self.w3afcore.target.set_options(target_opts)

        plugin_inst = factory(self.PLUGIN)
        plugin_inst.set_url_opener(self.w3afcore.uri_opener)
        plugin_inst.set_worker_pool(self.w3afcore.worker_pool)

        self.w3afcore.plugins.plugins['crawl'] = [plugin_inst]
        self.w3afcore.plugins._plugins_names_dict['crawl'] = ['exception_raise']
        self.exception_plugin = plugin_inst
        
        # Verify env and start the scan
        self.w3afcore.plugins.initialized = True
        self.w3afcore.verify_environment()        
    
    def tearDown(self):
        self.w3afcore.quit()
                        
    def test_stop_on_must_stop_exception(self):
        """
        Verify that the ScanMustStopException stops the scan.
        """
        self.exception_plugin.exception_to_raise = ScanMustStopException
        
        with patch('w3af.core.controllers.w3afCore.om.out') as om_mock:
            self.w3afcore.start()
            
            error = ('The following error was detected and could not be'
                     ' resolved:\nTest exception.\n')
            self.assertIn(call.error(error), om_mock.mock_calls)

    def test_stop_unknown_exception(self):
        """
        Verify that the ScanMustStopByUnknownReasonExc stops the scan.
        """
        self.exception_plugin.exception_to_raise = ScanMustStopByUnknownReasonExc
        self.assertRaises(ScanMustStopByUnknownReasonExc, self.w3afcore.start)
                
    def test_stop_by_user_request(self):
        """
        Verify that the ScanMustStopByUserRequest stops the scan.
        """
        self.exception_plugin.exception_to_raise = ScanMustStopByUserRequest
        
        with patch('w3af.core.controllers.w3afCore.om.out') as om_mock:
            self.w3afcore.start()
            
            message = 'Test exception.'
            self.assertIn(call.information(message), om_mock.mock_calls)