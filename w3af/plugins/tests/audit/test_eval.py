"""
test_eval.py

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
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.controllers.ci.mcir import get_mcir_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig


class TestEval(PluginTest):

    target_echo = get_moth_http('/audit/eval_vuln/eval_double.py')
    target_delay = get_moth_http('/audit/eval_vuln/eval_blind.py')

    _run_configs = {
        'echo': {
            'target': target_echo + '?text=1',
            'plugins': {
                'audit': (PluginConfig('eval',
                                       ('use_echo', True, PluginConfig.BOOL),
                                       ('use_time_delay', False, PluginConfig.BOOL)),
                          ),
            }
        },

        'delay': {
            'target': target_delay + '?text=1',
            'plugins': {
                'audit': (PluginConfig('eval',
                                       ('use_echo', False, PluginConfig.BOOL),
                                       ('use_time_delay', True, PluginConfig.BOOL)),
                          ),
            }
        }
    }

    def test_found_eval_echo(self):
        cfg = self._run_configs['echo']
        self._scan(cfg['target'], cfg['plugins'])

        vulns = self.kb.get('eval', 'eval')
        self.assertEquals(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals('eval() input injection vulnerability',
                          vuln.get_name())
        self.assertEquals("text", vuln.get_token_name())
        self.assertEquals(self.target_echo, str(vuln.get_url()))

    def test_found_eval_delay(self):
        cfg = self._run_configs['delay']
        self._scan(cfg['target'], cfg['plugins'])

        vulns = self.kb.get('eval', 'eval')
        self.assertEquals(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals('eval() input injection vulnerability',
                          vuln.get_name())
        self.assertEquals("text", vuln.get_token_name())
        self.assertEquals(self.target_delay, str(vuln.get_url()))


class TestPHPEchoEval(PluginTest):

    target = get_mcir_http('/phpwn/eval.php?sanitization_level=none'
                           '&sanitization_type=keyword'
                           '&sanitization_params='
                           '&query_results=all_rows'
                           '&error_level=verbose'
                           '&inject_string=abc'
                           '&location=value'
                           '&custom_inject='
                           '&submit=Inject%21')

    config = {'audit': (PluginConfig('eval',
                                    ('use_echo', True, PluginConfig.BOOL),
                                    ('use_time_delay', False, PluginConfig.BOOL)),),
    }

    def test_found_eval_echo_php(self):
        self._scan(self.target, self.config)

        vulns = self.kb.get('eval', 'eval')
        self.assertEquals(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals('eval() input injection vulnerability',
                          vuln.get_name())
        self.assertEquals('custom_inject', vuln.get_token_name())


class TestPHPSleepEval(PluginTest):

    target = get_mcir_http('/phpwn/eval.php?sanitization_level=none'
                           '&sanitization_type=keyword'
                           '&sanitization_params='
                           '&query_results=none'
                           '&error_level=none'
                           '&inject_string=123'
                           '&location=value'
                           '&custom_inject='
                           '&submit=Inject%21')

    config = {'audit': (PluginConfig('eval',
                                    ('use_echo', False, PluginConfig.BOOL),
                                    ('use_time_delay', True, PluginConfig.BOOL)),),
    }

    def test_found_eval_echo_php(self):
        self._scan(self.target, self.config)

        vulns = self.kb.get('eval', 'eval')
        self.assertEquals(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals('eval() input injection vulnerability',
                          vuln.get_name())
        self.assertEquals('custom_inject', vuln.get_token_name())
