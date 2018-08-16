"""
test_password_profiling.py

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
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.plugins.grep.password_profiling import password_profiling

from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL


class TestPasswordProfiling(PluginTest):

    password_profiling_url = get_moth_http('/grep/password_profiling/')

    _run_configs = {
        'cfg1': {
            'target': password_profiling_url,
            'plugins': {
                'grep': (PluginConfig('password_profiling'),),
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL)),
                )

            }
        }
    }

    def test_collected_passwords(self):
        cfg = self._run_configs['cfg1']
        self._scan(cfg['target'], cfg['plugins'])
        
        def sortfunc(x_obj, y_obj):
            return cmp(x_obj[1], y_obj[1])

        # pylint: disable=E1103
        # Pylint fails to detect the object types that come out of the KB            
        collected_passwords = self.kb.raw_read('password_profiling',
                                               'password_profiling')

        collected_passwords = collected_passwords.keys()
        # pylint: enable=E1103
        collected_passwords.sort(sortfunc)

        self.assertIn('Moth', collected_passwords)
        self.assertIn('application', collected_passwords)
        self.assertIn('creators', collected_passwords)

    def test_merge_password_profiling(self):
        pp = password_profiling()
        
        old_data = {'foobar': 1, 'spameggs': 2}
        data = {'charlotte': 3, 'and': 55, 'spameggs': 1}
        lang = 'en'
        
        url = URL('http://moth/')
        request = FuzzableRequest(url)
        
        merged_map = pp.merge_maps(old_data, data, request, lang)
        
        self.assertEqual(merged_map, {'foobar': 1,
                                      'spameggs': 3,
                                      'charlotte': 3})

    def test_merge_password_profiling_unknown_lang(self):
        pp = password_profiling()
        
        old_data = {'foobar': 1, 'spameggs': 2}
        data = {'charlotte': 3, 'and': 55, 'spameggs': 1}
        lang = 'hu'
        
        url = URL('http://moth/')
        request = FuzzableRequest(url)
        
        merged_map = pp.merge_maps(old_data, data, request, lang)
        
        self.assertEqual(merged_map, {'foobar': 1,
                                      'spameggs': 3,
                                      'charlotte': 3})

