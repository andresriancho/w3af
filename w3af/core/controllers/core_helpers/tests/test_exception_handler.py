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
import sys
import cPickle
import unittest
import threading

from nose.plugins.attrib import attr

from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.controllers.core_helpers.exception_handler import ExceptionHandler, ExceptionData
from w3af.core.controllers.core_helpers.status import CoreStatus
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.generic.kv_container import KeyValueContainer


class TestExceptionHandler(unittest.TestCase):

    EXCEPT_START = 'A "Exception" exception was found'

    def setUp(self):
        self.exception_handler = ExceptionHandler()
        self.exception_handler.clear()

        self.status = FakeStatus(None)
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
            self.exception_handler.handle(self.status,
                                          e,
                                          exec_info,
                                          enabled_plugins)

        scan_id = self.exception_handler.get_scan_id()
        self.assertTrue(scan_id)

        all_edata = self.exception_handler.get_all_exceptions()

        self.assertEqual(1, len(all_edata))

        edata = all_edata[0]

        self.assertTrue(edata.get_summary().startswith(self.EXCEPT_START))
        self.assertTrue('traceback' in edata.get_details())
        self.assertEquals(edata.plugin, 'plugin')
        self.assertEquals(edata.phase, 'phase')
        self.assertEquals(edata.fuzzable_request, 'http://www.w3af.org/')
        self.assertEquals(edata.filename, 'test_exception_handler.py')
        self.assertEquals(edata.exception_msg, str(e))
        self.assertEquals(edata.exception_class, e.__class__.__name__)
        # This is very very very dependant on changes to this file, but it was
        # the only way to do it without much effort
        self.assertEquals(edata.lineno, 50)

    @attr('smoke')
    def test_handle_multiple(self):

        for _ in xrange(10):
            try:
                raise Exception('unittest')
            except Exception, e:
                exec_info = sys.exc_info()
                enabled_plugins = ''
                self.exception_handler.handle(self.status, e, exec_info,
                                              enabled_plugins)

        self.exception_handler.get_scan_id()
        all_edata = self.exception_handler.get_all_exceptions()

        self.assertEqual(self.exception_handler.MAX_EXCEPTIONS_PER_PLUGIN,
                         len(all_edata))

        edata = all_edata[0]

        self.assertTrue(edata.get_summary().startswith(self.EXCEPT_START))
        self.assertTrue('traceback' in edata.get_details())
        self.assertEquals(edata.plugin, 'plugin')
        self.assertEquals(edata.phase, 'phase')
        self.assertEquals(edata.fuzzable_request, 'http://www.w3af.org/')
        self.assertEquals(edata.filename, 'test_exception_handler.py')

    def test_get_unique_exceptions(self):

        for _ in xrange(10):
            try:
                raise Exception('unittest')
            except Exception, e:
                exec_info = sys.exc_info()
                enabled_plugins = ''
                self.exception_handler.handle(self.status, e, exec_info,
                                              enabled_plugins)

        all_edata = self.exception_handler.get_all_exceptions()
        self.assertEqual(self.exception_handler.MAX_EXCEPTIONS_PER_PLUGIN,
                         len(all_edata))

        unique_edata = self.exception_handler.get_unique_exceptions()
        self.assertEqual(1, len(unique_edata))

        edata = unique_edata[0]

        self.assertTrue(edata.get_summary().startswith(self.EXCEPT_START))
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

        self.assertTrue(edata.get_summary().startswith(self.EXCEPT_START))
        self.assertTrue('traceback' in edata.get_details())
        self.assertEquals(edata.plugin, 'plugin')
        self.assertEquals(edata.phase, 'phase')
        self.assertEquals(edata.fuzzable_request, 'http://www.w3af.org/')
        self.assertEquals(edata.filename, 'test_exception_handler.py')
        # This is very very very dependant on changes to this file, but it was
        # the only way to do it without much effort
        self.assertEquals(edata.lineno, 137)

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
        self.assertEquals(edata.lineno, 170)


class FakeStatus(CoreStatus):
    pass


class TestExceptionData(unittest.TestCase):

    def get_fuzzable_request(self):
        headers = Headers([(u'Hello', u'World')])
        post_data = KeyValueContainer(init_val=[('a', ['b'])])
        url = URL('http://w3af.org')
        return FuzzableRequest(url, method='GET', post_data=post_data,
                               headers=headers)

    def test_without_traceback(self):
        tb = None
        enabled_plugins = '{}'

        fr = self.get_fuzzable_request()

        core = w3afCore()
        status = CoreStatus(core)
        status.set_running_plugin('audit', 'sqli', log=False)
        status.set_current_fuzzable_request('audit', fr)

        exception_data = ExceptionData(status,
                                       KeyError(),
                                       tb,
                                       enabled_plugins,
                                       store_tb=False)

        pickled_ed = cPickle.dumps(exception_data)
        unpickled_ed = cPickle.loads(pickled_ed)

        self.assertEqual(exception_data.to_json(),
                         unpickled_ed.to_json())

    def test_serialize_deserialize(self):
        try:
            raise KeyError
        except Exception, e:
            except_type, except_class, tb = sys.exc_info()
            enabled_plugins = '{}'

            fr = self.get_fuzzable_request()

            core = w3afCore()
            status = CoreStatus(core)
            status.set_running_plugin('audit', 'sqli', log=False)
            status.set_current_fuzzable_request('audit', fr)

            exception_data = ExceptionData(status,
                                           e,
                                           tb,
                                           enabled_plugins,
                                           store_tb=False)

            pickled_ed = cPickle.dumps(exception_data)
            unpickled_ed = cPickle.loads(pickled_ed)

            self.assertEqual(exception_data.to_json(),
                             unpickled_ed.to_json())

    def test_fail_traceback_serialize(self):
        try:
            raise KeyError
        except Exception, e:
            except_type, except_class, tb = sys.exc_info()
            enabled_plugins = '{}'

            fr = self.get_fuzzable_request()

            core = w3afCore()
            status = CoreStatus(core)
            status.set_running_plugin('audit', 'sqli', log=False)
            status.set_current_fuzzable_request('audit', fr)

            exception_data = ExceptionData(status,
                                           e,
                                           tb,
                                           enabled_plugins,
                                           store_tb=True)

            self.assertRaises(TypeError, cPickle.dumps, exception_data)
