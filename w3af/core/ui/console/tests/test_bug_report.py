"""
test_bug_report.py

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
import os
import re
import shutil

from github import Github
from nose.plugins.attrib import attr

from w3af import ROOT_PATH
from w3af.core.ui.console.console_ui import ConsoleUI
from w3af.core.ui.console.tests.helper import ConsoleTestHelper

from w3af.core.controllers.misc.file_lock import FileLock
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.controllers.easy_contribution.github_issues import OAUTH_TOKEN


@attr('moth')
@attr('internet')
class TestConsoleBugReport(ConsoleTestHelper):
    """
    Run a scan from the console UI (which fails with a bug) and report it to
    a github issue.
    """
    
    def setUp(self):
        """
        This is a rather complex setUp since I need to move the failing_spider.py
        plugin to the plugin directory in order to be able to run it afterwards.

        In the tearDown method, I'll remove the file.
        """
        self.src = os.path.join(ROOT_PATH, 'plugins', 'tests', 'crawl',
                                'failing_spider.py')
        self.dst = os.path.join(ROOT_PATH, 'plugins', 'crawl',
                                'failing_spider.py')

        # This lock prevents others (which also implement the locking) from
        # removing our file
        self.lock = FileLock(self.dst, timeout=60)
        self.lock.acquire()

        shutil.copy(self.src, self.dst)

        super(TestConsoleBugReport, self).setUp()

    def tearDown(self):
        if os.path.exists(self.dst):
            os.remove(self.dst)
        
        # pyc file
        if os.path.exists(self.dst + 'c'):
            os.remove(self.dst + 'c')

        # Allow others to create the failing_spider.py file
        self.lock.release()

        super(TestConsoleBugReport, self).tearDown()
        
    def test_buggy_scan(self):
        target = get_moth_http('/grep/csp/')
        commands_to_run = ['plugins',
                           'output console',
                           
                           'crawl failing_spider',
                                'crawl config failing_spider',
                                'set only_forward true',
                           'back',
                           
                           'grep path_disclosure',
                           'back',
                           
                           'target',
                           'set target %s' % (target),
                           'back',
                           
                           'start',
                           
                           'bug-report',
                           'summary',
                           'report',
                           
                           'exit']

        expected = ('During the current scan (with id: ',
                    'A "Exception" exception was found while running crawl.failing_spider on ',
                    'New URL found by failing_spider plugin: ',
                    '    [1/1] Bug with id 0 reported at https://github.com/andresriancho/w3af/issues/')

        self.console = ConsoleUI(commands=commands_to_run, do_upd=False)
        self.console.sh()

        caught_exceptions = self.console._w3af.exception_handler.get_all_exceptions()
        self.assertEqual(len(caught_exceptions), 1, self._mock_stdout.messages)
        
        assert_result, msg = self.startswith_expected_in_output(expected)
        self.assertTrue(assert_result, msg)

        found_errors = self.error_in_output(['No such file or directory'])

        self.assertFalse(found_errors)
        
        # Clear the exceptions, we don't need them anymore.
        self.console._w3af.exception_handler.clear()
        
        # Close issue from github
        issue_id_re = re.compile('https://github.com/andresriancho/w3af/issues/(\d*)')
        for line in self._mock_stdout.messages:
            mo = issue_id_re.search(line)
            if mo is not None:
                issue_id = mo.group(1)
                
                gh = Github(OAUTH_TOKEN)
                repo = gh.get_user('andresriancho').get_repo('w3af')
                issue = repo.get_issue(int(issue_id))
                issue.edit(state='closed')                 
                
                break
        else:
            self.assertTrue(False, 'Did NOT close test ticket.')