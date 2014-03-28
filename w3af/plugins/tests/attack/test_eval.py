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

from w3af.plugins.tests.helper import PluginConfig, ExecExploitTest
from w3af.core.data.kb.vuln_templates.eval_template import EvalTemplate


class TestEvalShell(ExecExploitTest):

    EVAL = get_moth_http('/audit/eval_vuln/eval_double.py?text=1')

    _run_configs = {
        'eval': {
            'target': EVAL,
            'plugins': {
                'audit': (PluginConfig('eval'),),
            }
        },
    }

    def test_found_exploit_eval(self):
        # Run the scan
        cfg = self._run_configs['eval']
        self._scan(cfg['target'], cfg['plugins'])

        # Assert the general results
        vulns = self.kb.get('eval', 'eval')
        self.assertEquals(1, len(vulns))
        
        vuln = vulns[0]
        
        self.assertEquals("eval() input injection vulnerability", vuln.get_name())
        self.assertEquals('eval_double.py', vuln.get_url().get_file_name())

        vuln_to_exploit_id = vuln.get_id()
        self._exploit_vuln(vuln_to_exploit_id, 'eval')

    def test_from_template(self):
        et = EvalTemplate()
        
        options = et.get_options()
        options['url'].set_value(get_moth_http('/audit/eval_vuln/eval_double.py'))
        options['data'].set_value('text=1')
        options['vulnerable_parameter'].set_value('text')
        et.set_options(options)

        et.store_in_kb()
        vuln = self.kb.get(*et.get_kb_location())[0]
        vuln_to_exploit_id = vuln.get_id()
        
        self._exploit_vuln(vuln_to_exploit_id, 'eval')