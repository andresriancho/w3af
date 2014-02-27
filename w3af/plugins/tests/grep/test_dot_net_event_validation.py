"""
test_dot_net_event_validation.py

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
from nose.plugins.attrib import attr

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig


@attr('ci_ready')
class TestEventValidation(PluginTest):

    dot_net_event_validation_url = get_moth_http('/grep/dot_net_event_validation/')

    _run_configs = {
        'cfg1': {
            'target': dot_net_event_validation_url,
            'plugins': {
                'grep': (PluginConfig('dot_net_event_validation'),),
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL)),
                )

            }
        }
    }

    def test_found_vuln(self):
        cfg = self._run_configs['cfg1']
        self._scan(cfg['target'], cfg['plugins'])
        vulns = self.kb.get('dot_net_event_validation',
                            'dot_net_event_validation')

        self.assertEquals(3, len(vulns), vulns)

        EXPECTED_VULNS = set(
            [('event_validation.html', 'decode the viewstate contents.'),
             ('without_event_validation.html',
              'decode the viewstate contents.'),
             ('without_event_validation.html', 'r should be manually verified.')])

        vulns_set = set()
        for vuln in vulns:
            ending = vuln.get_desc(with_id=False)[-30:]
            vulns_set.add((vuln.get_url().get_file_name(), ending))

        self.assertEqual(EXPECTED_VULNS,
                         vulns_set)
