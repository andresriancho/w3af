'''
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
'''
import unittest
import os
import shutil

from mock import patch, call
from nose.plugins.attrib import attr

from w3af.core.data.parsers.url import URL
from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.controllers.exceptions import (w3afMustStopException,
                                         w3afMustStopByUnknownReasonExc,
                                         w3afMustStopByUserRequest)
from w3af.plugins.tests.helper import create_target_option_list


@attr('moth')
class TestCoreExceptions(unittest.TestCase):
    '''
    TODO: Think about mocking all calls to ExtendedUrllib in order to avoid
          being tagged as 'moth'.
    '''
    def setUp(self):
        '''
        This is a rather complex setUp since I need to move the
        exception_raise.py plugin to the plugin directory in order to be able
        to run it afterwards.

        In the tearDown method, I'll remove the file.
        '''
        self.src = os.path.join('core', 'controllers', 'tests', 'exception_raise.py')
        self.dst = os.path.join('plugins', 'crawl', 'exception_raise.py')
        shutil.copy(self.src, self.dst)

        self.w3afcore = w3afCore()
        
        target_opts = create_target_option_list(URL('http://moth/'))
        self.w3afcore.target.set_options(target_opts)

        self.w3afcore.plugins.set_plugins(['exception_raise',], 'crawl')

        # Verify env and start the scan
        self.w3afcore.plugins.init_plugins()
        self.w3afcore.verify_environment()
        
        self.exception_plugin = self.w3afcore.plugins.plugins['crawl'][0]
        
    
    def tearDown(self):
        self.w3afcore.quit()
        
        # py and pyc file
        for fname in (self.dst, self.dst + 'c'):
            if os.path.exists(fname):
                os.remove(fname)
                
    def test_stop_on_must_stop_exception(self):
        '''
        Verify that the w3afMustStopException stops the scan.
        '''
        self.exception_plugin.exception_to_raise = w3afMustStopException
        
        with patch('core.controllers.w3afCore.om.out') as om_mock:
            self.w3afcore.start()
            
            error = "\n**IMPORTANT** The following error was detected by w3af"\
                    " and couldn't be resolved:\nTest exception.\n"
            self.assertIn(call.error(error), om_mock.mock_calls)

    def test_stop_unknown_exception(self):
        '''
        Verify that the w3afMustStopByUnknownReasonExc stops the scan.
        '''
        self.exception_plugin.exception_to_raise = w3afMustStopByUnknownReasonExc
        self.assertRaises(w3afMustStopByUnknownReasonExc, self.w3afcore.start)
                
    def test_stop_by_user_request(self):
        '''
        Verify that the w3afMustStopByUserRequest stops the scan.
        '''
        self.exception_plugin.exception_to_raise = w3afMustStopByUserRequest
        
        with patch('core.controllers.w3afCore.om.out') as om_mock:
            self.w3afcore.start()
            
            message = 'Test exception.'
            self.assertIn(call.information(message), om_mock.mock_calls)