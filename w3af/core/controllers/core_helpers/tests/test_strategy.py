"""
test_strategy.py

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
import subprocess
import sys
import os
import re

from nose.plugins.attrib import attr

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.controllers.ci.wavsep import get_wavsep_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.controllers.ci.detect import is_running_on_ci
from w3af.core.data.db.startup_cfg import StartUpConfig

SCRIPT_PATH = '/tmp/script-1557.w3af'
OUTPUT_PATH = '/tmp/1557-output-w3af.txt'
TEST_SCRIPT_1557 = """\
plugins

output console,text_file

output config console
set verbose False
back

output config text_file
set output_file %s
set verbose True
back

audit xss

crawl web_spider
crawl config web_spider
set only_forward True
back

back
target
set target %swavsep/active/Reflected-XSS/RXSS-Detection-Evaluation-GET/
back

start

exit
"""


class TestStrategy(PluginTest):
    def setUp(self):
        super(TestStrategy, self).setUp()

        startup_cfg = StartUpConfig()
        startup_cfg.accepted_disclaimer = True
        startup_cfg.save()

    def tearDown(self):
        super(TestStrategy, self).tearDown()

        if os.path.exists(SCRIPT_PATH):
            os.unlink(SCRIPT_PATH)

        # Add a return right below this line if you want the logs for debugging
        if os.path.exists(OUTPUT_PATH):
            os.unlink(OUTPUT_PATH)

    def test_1557_random_number_of_results(self):
        """
        Pseudo-random number of vulnerabilities found in audit phase (xss)

        https://github.com/andresriancho/w3af/issues/1557
        """
        script = TEST_SCRIPT_1557 % (OUTPUT_PATH, get_wavsep_http())
        file(SCRIPT_PATH, 'w').write(script)

        python_executable = sys.executable

        VULN_STRING = 'A Cross Site Scripting vulnerability was found at'
        URL_VULN_RE = re.compile('%s: "(.*?)"' % VULN_STRING)
        all_previous_vulns = []

        loops = 2 if is_running_on_ci() else 10

        for i in xrange(loops):
            print('Start run #%s' % i)
            found_vulns = set()

            p = subprocess.Popen([python_executable, 'w3af_console',
                                  '-n', '-s', SCRIPT_PATH],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 shell=False,
                                 universal_newlines=True)

            stdout, stderr = p.communicate()
            i_vuln_count = stdout.count(VULN_STRING)
            print('%s vulnerabilities found' % i_vuln_count)

            self.assertNotEqual(i_vuln_count, 0, stdout)

            for line in stdout.split('\n'):
                if VULN_STRING in line:
                    found_vulns.add(URL_VULN_RE.search(line).group(1))

            for previous_found in all_previous_vulns:
                self.assertEqual(found_vulns, previous_found)

            all_previous_vulns.append(found_vulns)


class TestSameFuzzableRequestSet(PluginTest):
    target_url = get_moth_http('/audit/sql_injection/'
                               'where_string_single_qs.py?uname=pablo')

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (PluginConfig('sqli'),),
            }
        }
    }

    @attr('smoke')
    @attr('moth')
    def test_same_fr_set_object(self):
        cfg = self._run_configs['cfg']

        id_before_fr = id(self.kb.get_all_known_fuzzable_requests())
        id_before_ur = id(self.kb.get_all_known_urls())

        self._scan(cfg['target'], cfg['plugins'])

        id_after_fr = id(self.kb.get_all_known_fuzzable_requests())
        id_after_ur = id(self.kb.get_all_known_urls())

        self.assertEquals(id_before_fr, id_after_fr)
        self.assertEquals(id_before_ur, id_after_ur)