"""
test_strategy_low_level.py

Copyright 2013 Andres Riancho

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
import re
import unittest
import threading
import httpretty

from mock import Mock
from nose.plugins.attrib import attr

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.controllers.core_helpers.strategy import CoreStrategy
from w3af.core.controllers.exceptions import ScanMustStopException
from w3af.core.data.kb.knowledge_base import kb


@attr('moth')
class TestStrategy(unittest.TestCase):
    
    TARGET_URL = get_moth_http('/audit/sql_injection/'
                               'where_integer_qs.py?id=1')

    def setUp(self):
        kb.cleanup()

    def test_strategy_run(self):
        core = w3afCore()
        
        target = core.target.get_options()
        target['target'].set_value(self.TARGET_URL)
        core.target.set_options(target)
        
        core.plugins.set_plugins(['sqli'], 'audit')
        core.plugins.init_plugins()
        
        core.verify_environment()
        core.scan_start_hook()
        
        def verify_threads_running(functor):
            thread_names = [t.name for t in threading.enumerate()]
            self.assertIn('WorkerThread', thread_names)
            self.called_teardown_audit = True
            return functor
        
        self.called_teardown_audit = False
        
        strategy = CoreStrategy(core)
        strategy._teardown_audit = verify_threads_running(strategy._teardown_audit)
        
        strategy.start()
        
        # Now test that those threads are being terminated
        self.assertTrue(self.called_teardown_audit)
        
        vulns = kb.get('sqli', 'sqli')
        self.assertEqual(len(vulns), 1, vulns)
        
        # Tell the core that we've finished, this should kill the WorkerThreads
        core.exploit_phase_prerequisites = lambda: 42
        core.scan_end_hook()

        self._assert_thread_names()

    def _assert_thread_names(self):
        """
        Makes sure that the threads which are living in my process are the
        ones that I want.
        """
        threads = [t for t in threading.enumerate()]
        thread_names = [t.name for t in threads]

        thread_names_set = set(thread_names)
        expected_names = {'PoolTaskHandler',
                          'PoolResultHandler',
                          'WorkerThread',
                          'PoolWorkerHandler',
                          'MainThread',
                          'SQLiteExecutor',
                          'OutputManager',
                          'QueueFeederThread'}

        self.assertEqual(thread_names_set, expected_names)

    def test_strategy_exception(self):
        core = w3afCore()
        
        target = core.target.get_options()
        target['target'].set_value(self.TARGET_URL)
        core.target.set_options(target)
        
        core.plugins.set_plugins(['sqli'], 'audit')
        core.plugins.init_plugins()
        
        core.verify_environment()
        core.scan_start_hook()
        
        strategy = CoreStrategy(core)
        strategy._fuzzable_request_router = Mock(side_effect=Exception)
        
        strategy.terminate = Mock(wraps=strategy.terminate)
        
        self.assertRaises(Exception, strategy.start)
        
        # Now test that those threads are being terminated
        self.assertEqual(strategy.terminate.called, True)
        
        core.exploit_phase_prerequisites = lambda: 42
        core.scan_end_hook()

        self._assert_thread_names()
        
    def test_strategy_verify_target_server_up(self):
        core = w3afCore()
        
        # TODO: Change 2312 by an always closed/non-http port
        INVALID_TARGET = 'http://localhost:2312/'
        
        target = core.target.get_options()
        target['target'].set_value(INVALID_TARGET)
        core.target.set_options(target)
        
        core.plugins.set_plugins(['sqli'], 'audit')
        core.plugins.init_plugins()
        
        core.verify_environment()
        core.scan_start_hook()
        
        strategy = CoreStrategy(core)
        
        try:
            strategy.start()
        except ScanMustStopException, wmse:
            message = str(wmse)
            self.assertIn('Please verify your target configuration', message)
        else:
            self.assertTrue(False)

    @httpretty.activate
    def test_alert_if_target_is_301_all_proto_redir(self):
        """
        Tests that the protocol redirection is detected and reported in
        the kb
        """
        core = w3afCore()

        httpretty.register_uri(httpretty.GET,
                               re.compile("w3af.com/(.*)"),
                               body='301',
                               status=301,
                               adding_headers={'Location': 'https://w3af.com/'})

        target = core.target.get_options()
        target['target'].set_value('http://w3af.com/')
        core.target.set_options(target)

        core.plugins.set_plugins(['sqli'], 'audit')
        core.plugins.init_plugins()

        core.verify_environment()
        core.scan_start_hook()

        strategy = CoreStrategy(core)
        strategy.start()

        infos = kb.get('core', 'core')
        self.assertEqual(len(infos), 1, infos)

    @httpretty.activate
    def test_alert_if_target_is_301_all_domain_redir(self):
        """
        Tests that the domain redirection is detected and reported in
        the kb
        """
        core = w3afCore()

        httpretty.register_uri(httpretty.GET,
                               re.compile("w3af.com/(.*)"),
                               body='301',
                               status=301,
                               adding_headers={'Location': 'http://www.w3af.com/'})

        target = core.target.get_options()
        target['target'].set_value('http://w3af.com/')
        core.target.set_options(target)

        core.plugins.set_plugins(['sqli'], 'audit')
        core.plugins.init_plugins()

        core.verify_environment()
        core.scan_start_hook()

        strategy = CoreStrategy(core)
        strategy.start()

        infos = kb.get('core', 'core')
        self.assertEqual(len(infos), 1, infos)

    @httpretty.activate
    def test_alert_if_target_is_301_all_internal_redir(self):
        """
        Tests that no info is created if the site redirects internally
        """
        core = w3afCore()

        httpretty.register_uri(httpretty.GET,
                               re.compile("w3af.com/(.*)"),
                               body='301',
                               status=301,
                               adding_headers={'Location': 'http://w3af.com/xyz'})

        target = core.target.get_options()
        target['target'].set_value('http://w3af.com/')
        core.target.set_options(target)

        core.plugins.set_plugins(['sqli'], 'audit')
        core.plugins.init_plugins()

        core.verify_environment()
        core.scan_start_hook()

        strategy = CoreStrategy(core)
        strategy.start()

        infos = kb.get('core', 'core')
        self.assertEqual(len(infos), 0, infos)
