'''
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
'''
from plugins.tests.helper import PluginTest, PluginConfig


class TestPasswordProfiling(PluginTest):

    password_profiling_url = 'https://moth/w3af/grep/password_profiling/'

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

        self.assertEquals(collected_passwords[0], 'Password')
        self.assertTrue('repeat' in collected_passwords)
