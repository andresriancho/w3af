'''
test_consoleui.py

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
import sys
import unittest

from nose.plugins.attrib import attr

from core.ui.consoleUi.consoleUi import consoleUi


def do_nothing(self, *args, **kwds):
    pass
    
class mock_stdout(object):
    def __init__(self):
        self.messages = []
    
    def write(self, msg):
        self.messages.extend( msg.split('\n\r') )
    
    flush = do_nothing
    
    def clear(self):
        self.messages = []

@attr('smoke')
class TestConsoleUI(unittest.TestCase):
    '''
    Basic test for the console UI.
    '''
    def setUp(self):
        self.mock_sys()
        
    def tearDown(self):
        self.restore_sys()

    def mock_sys(self):
        # backup
        self.old_stdout = sys.stdout
        self.old_exit = sys.exit
        
        # assign new
        self._mock_stdout = mock_stdout()
        sys.stdout = self._mock_stdout
        sys.exit = do_nothing

    def restore_sys(self):
        sys.stdout = self.old_stdout
        sys.exit = self.old_exit
    
    def test_menu_browse(self):
        MENU_EXPECTED = (
                         ('misc-settings',('w3af>>> ','w3af/config:misc-settings>>> ') ),
                         ('http-settings',('w3af>>> ','w3af/config:http-settings>>> ') ),
                         ('target',('w3af>>> ','w3af/config:target>>> ') )
                         )
        
        for menu, expected in MENU_EXPECTED:
            commands_to_run = [menu, 'back', 'exit']
            
            self.mock_sys()
            
            console = consoleUi(commands=commands_to_run, do_upd=False)
            console.sh()
            
            self.restore_sys()
            
            self.assertTrue( self.all_expected_in_output(expected), 
                             self._mock_stdout.messages )
            
            self._mock_stdout.clear()
    
    def test_menu_plugin_desc(self):
        commands_to_run = ['plugins',
                           'infrastructure desc zone_h',
                           'back', 
                           'exit']
        
        expected = ('This plugin searches the zone-h.org',
                    'result. The information stored in',
                    'previous defacements to the target website.')
        
        self.mock_sys()
        
        console = consoleUi(commands=commands_to_run, do_upd=False)
        console.sh()
        
        self.restore_sys()
        
        self.assertTrue( self.startswith_expected_in_output(expected), 
                         self._mock_stdout.messages )
        
        self._mock_stdout.clear()        
    
    def test_SQL_scan(self):
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
                                'set target http://moth/w3af/audit/sql_injection/select/sql_injection_string.php?name=andres', 'back',
                            'start',
                            'exit']
        
        expected = ('SQL injection in ',
                    'A SQL error was found in the response supplied by ',
                    'New URL found by web_spider plugin: http://moth/w3af/audit/sql_injection/select/sql_injection_string.php')
        
        self.mock_sys()
        
        console = consoleUi(commands=commands_to_run, do_upd=False)
        console.sh()
        
        self.restore_sys()
        
        self.assertTrue( self.startswith_expected_in_output(expected), 
                         self._mock_stdout.messages )
        
        self._mock_stdout.clear()
        
    def test_load_profile_exists(self):
        commands_to_run = ['profiles',
                           'help',
                           'use OWASP_TOP10',
                           'exit']
        
        expected = ('The plugins configured by the scan profile have been enabled',
                    'Please set the target URL',
                    '| use                            | Use a profile.')
        
        self.mock_sys()
        
        console = consoleUi(commands=commands_to_run, do_upd=False)
        console.sh()
        
        self.restore_sys()
        
        self.assertTrue( self.startswith_expected_in_output(expected), 
                         self._mock_stdout.messages )
        
        self._mock_stdout.clear()

    def test_load_profile_not_exists(self):
        commands_to_run = ['profiles',
                           'help',
                           'use do_not_exist',
                           'exit']
        
        expected = ('Unknown profile name: "do_not_exist"',)
        
        self.mock_sys()
        
        console = consoleUi(commands=commands_to_run, do_upd=False)
        console.sh()
        
        self.restore_sys()
        
        self.assertTrue( self.startswith_expected_in_output(expected), 
                         self._mock_stdout.messages )
        
        self._mock_stdout.clear()
        
    def startswith_expected_in_output(self, expected):
        for line in expected:
            for sys_line in self._mock_stdout.messages:
                if sys_line.startswith(line):
                    break
            else:
                return False
        else:
            return True
            
    def all_expected_in_output(self, expected):
        for line in expected:
            if line not in self._mock_stdout.messages:
                return False
        else:
            return True
        