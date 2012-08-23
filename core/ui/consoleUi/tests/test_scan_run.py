'''
test_scan_run.py

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
from nose.plugins.attrib import attr

from core.ui.consoleUi.consoleUi import consoleUi
from core.ui.consoleUi.tests.helper import ConsoleTestHelper


@attr('smoke')
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
                                'set fileName output-w3af.txt',
                                'set verbose True', 'back',
                           'output config console',
                                'set verbose False', 'back', 
                           'audit sqli',
                           'crawl web_spider',
                           'crawl config web_spider', 
                                'set onlyForward True', 'back',
                            'grep path_disclosure',
                            'back', 
                            'target',
                                'set target %s%s' % (target, qs), 'back',
                            'start',
                            'exit']
        
        expected = ('SQL injection in ',
                    'A SQL error was found in the response supplied by ',
                    'New URL found by web_spider plugin: "%s"' % target)
        
        console = consoleUi(commands=commands_to_run, do_upd=False)
        console.sh()
        
        self.assertTrue( self.startswith_expected_in_output(expected), 
                         self._mock_stdout.messages )
        
