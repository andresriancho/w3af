'''
test_scan_run.py

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
'''
from nose.plugins.attrib import attr

from core.ui.console.console_ui import ConsoleUI
from core.ui.console.tests.helper import ConsoleTestHelper


@attr('moth')
class TestScanRunConsoleUI(ConsoleTestHelper):
    '''
    Run scans from the console UI.
    '''

    def test_SQL_scan(self):
        target = 'http://moth/w3af/audit/sql_injection/select/sql_injection_string.php'
        qs = '?name=andres'
        commands_to_run = ['plugins',
                           'output console,text_file',
                           'output config text_file',
                           'set output_file %s' % self.OUTPUT_FILE,
                           'set http_output_file %s' % self.OUTPUT_HTTP_FILE,
                           'set verbose True', 'back',
                           'output config console',
                           'set verbose False', 'back',
                           'audit sqli',
                           'crawl web_spider',
                           'crawl config web_spider',
                           'set only_forward True', 'back',
                           'grep path_disclosure',
                           'back',
                           'target',
                           'set target %s%s' % (target, qs), 'back',
                           'start',
                           'exit']

        expected = ('SQL injection in ',
                    'A SQL error was found in the response supplied by ',
                    'New URL found by web_spider plugin: "%s"' % target)

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        assert_result, msg = self.startswith_expected_in_output(expected)
        self.assertTrue(assert_result, msg)

        found_errors = self.error_in_output(['No such file or directory',
                                             'Exception'])

        self.assertFalse(found_errors)

    @attr('smoke')
    def test_two_scans(self):
        target_1 = 'http://moth/w3af/audit/sql_injection/select/sql_injection_string.php'
        qs_1 = '?name=andres'
        scan_commands_1 = ['plugins',
                           'output console,text_file',
                           'output config text_file',
                           'set output_file %s' % self.OUTPUT_FILE,
                           'set http_output_file %s' % self.OUTPUT_HTTP_FILE,
                           'set verbose True', 'back',
                           'output config console',
                           'set verbose False', 'back',
                           'audit sqli',
                           'crawl web_spider',
                           'crawl config web_spider',
                           'set only_forward True', 'back',
                           'grep path_disclosure',
                           'back',
                           'target',
                           'set target %s%s' % (target_1, qs_1), 'back',
                           'start']

        expected_1 = ('SQL injection in ',
                      'A SQL error was found in the response supplied by ',
                      'New URL found by web_spider plugin: "%s"' % target_1)

        target_2 = 'http://moth/w3af/audit/xss/simple_xss.php'
        qs_2 = '?text=1'
        scan_commands_2 = ['plugins',
                           'output console,text_file',
                           'output config text_file',
                           'set output_file %s' % self.OUTPUT_FILE,
                           'set http_output_file %s' % self.OUTPUT_HTTP_FILE,
                           'set verbose True', 'back',
                           'output config console',
                           'set verbose False', 'back',
                           'audit xss',
                           'crawl web_spider',
                           'crawl config web_spider',
                           'set only_forward True', 'back',
                           'grep path_disclosure',
                           'back',
                           'target',
                           'set target %s%s' % (target_2, qs_2), 'back',
                           'start',
                           'exit']

        expected_2 = ('A Cross Site Scripting vulnerability was found at',
                      'New URL found by web_spider plugin: "%s"' % target_2)

        scan_commands = scan_commands_1 + scan_commands_2

        self.console = ConsoleUI(commands=scan_commands, do_upd=False)
        self.console.sh()

        assert_result, msg = self.startswith_expected_in_output(expected_1)
        self.assertTrue(assert_result, msg)

        assert_result, msg = self.startswith_expected_in_output(expected_2)
        self.assertTrue(assert_result, msg)

        found_errors = self.error_in_output(['No such file or directory',
                                             'Exception'])

        self.assertFalse(found_errors)
