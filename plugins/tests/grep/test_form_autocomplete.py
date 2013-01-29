'''
test_form_autocomplete.py

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

from plugins.tests.helper import PluginTest, PluginConfig


class TestFormAutocomplete(PluginTest):

    target_url = 'http://moth/w3af/grep/form_autocomplete/'

    _run_configs = {
        'cfg1': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('form_autocomplete'),),
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
        vulns = self.kb.get('form_autocomplete', 'form_autocomplete')

        expected_results = ["index-form-default.html",
                            "index-form-on.html",
                            "index-form-on-field-on.html"]

        self.assertEquals(3, len(vulns))

        filenames = [vuln.get_url().get_file_name() for vuln in vulns]
        filenames.sort()
        expected_results.sort()

        self.assertEquals(expected_results, filenames)
