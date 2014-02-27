# -*- coding: UTF-8 -*-
"""
test_exception_handler.py

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
import threading
import sys

from nose.plugins.attrib import attr

from w3af.core.controllers.core_helpers.exception_handler import ExceptionHandler
from w3af.core.controllers.core_helpers.status import w3af_core_status


class TestExceptionHandler(unittest.TestCase):

    def setUp(self):
        self.exception_handler = ExceptionHandler()
        self.exception_handler.clear()

        self.status = fake_status(None)
        self.status.set_running_plugin('phase', 'plugin')
        self.status.set_current_fuzzable_request('phase',
                                                 'http://www.w3af.org/')

    @attr('smoke')
    def test_handle_one(self):

        try:
            raise Exception('unittest')
        except Exception, e:
            exec_info = sys.exc_info()
            enabled_plugins = ''
            self.exception_handler.handle(self.status, e, exec_info,
                                          enabled_plugins)

        scan_id = self.exception_handler.get_scan_id()
        self.assertTrue(scan_id)

        all_edata = self.exception_handler.get_all_exceptions()

        self.assertEqual(1, len(all_edata))

        edata = all_edata[0]

        self.assertTrue(
            edata.get_summary().startswith('An exception was found'))
        self.assertTrue('traceback' in edata.get_details())
        self.assertEquals(edata.plugin, 'plugin')
        self.assertEquals(edata.phase, 'phase')
        self.assertEquals(edata.fuzzable_request, 'http://www.w3af.org/')
        self.assertEquals(edata.filename, 'test_exception_handler.py')
        self.assertEquals(edata.exception, e)
        # This is very very very dependant on changes to this file, but it was
        # the only way to do it without much effort
        self.assertEquals(edata.lineno, 48)

    @attr('smoke')
    def test_handle_multiple(self):

        for _ in xrange(10):
            try:
                raise Exception('unittest')
            except Exception, e:
                exec_info = sys.exc_info()
                enabled_plugins = ''
                self.exception_handler.handle(
                    self.status, e, exec_info, enabled_plugins)

        self.exception_handler.get_scan_id()
        all_edata = self.exception_handler.get_all_exceptions()

        self.assertEqual(
            self.exception_handler.MAX_EXCEPTIONS_PER_PLUGIN, len(all_edata))

        edata = all_edata[0]

        self.assertTrue(
            edata.get_summary().startswith('An exception was found'))
        self.assertTrue('traceback' in edata.get_details())
        self.assertEquals(edata.plugin, 'plugin')
        self.assertEquals(edata.phase, 'phase')
        self.assertEquals(edata.fuzzable_request, 'http://www.w3af.org/')
        self.assertEquals(edata.filename, 'test_exception_handler.py')

    def test_handle_threads_calls(self):
        
        def test2():
            raise Exception('unittest')
        
        def test(ehandler):
            try:
                test2()
            except Exception, e:
                exec_info = sys.exc_info()
                enabled_plugins = ''
                ehandler.handle(self.status, e, exec_info, enabled_plugins)

        th = threading.Thread(target=test, args=(self.exception_handler,))
        th.start()
        th.join()
        
        all_edata = self.exception_handler.get_all_exceptions()

        self.assertEqual(1, len(all_edata))

        edata = all_edata[0]

        self.assertTrue(
            edata.get_summary().startswith('An exception was found'))
        self.assertTrue('traceback' in edata.get_details())
        self.assertEquals(edata.plugin, 'plugin')
        self.assertEquals(edata.phase, 'phase')
        self.assertEquals(edata.fuzzable_request, 'http://www.w3af.org/')
        self.assertEquals(edata.filename, 'test_exception_handler.py')
        # This is very very very dependant on changes to this file, but it was
        # the only way to do it without much effort
        self.assertEquals(edata.lineno, 107)

    def test_handle_multi_calls(self):

        def test3():        
            raise Exception('unittest')
        
        def test2():
            test3()
        
        def test(ehandler):
            try:
                test2()
            except Exception, e:
                exec_info = sys.exc_info()
                enabled_plugins = ''
                ehandler.handle(self.status, e, exec_info, enabled_plugins)

        test(self.exception_handler)
        all_edata = self.exception_handler.get_all_exceptions()

        self.assertEqual(1, len(all_edata))

        edata = all_edata[0]

        # This is very very very dependant on changes to this file, but it was
        # the only way to do it without much effort
        self.assertEquals(edata.lineno, 141)        
                
class fake_status(w3af_core_status):
    pass
