'''
test_detailed.py

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
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.data.parsers.url import URL


class TestDetailed(PluginTest):

    base_url = 'http://moth/w3af/auth/detailed/'

    _run_config = {
        'target': base_url,
        'plugins': {
        'crawl': (
        PluginConfig('web_spider',
                     ('only_forward', True, PluginConfig.BOOL),
                     (
        'ignore_regex', '.*logout.*', PluginConfig.STR)),

        ),
            'audit': (PluginConfig('xss',),),
            'auth': (PluginConfig('detailed',
                                 ('username', 'admin', PluginConfig.STR),
                                 ('password', 'admin', PluginConfig.STR),
                                 ('username_field',
                                  'username', PluginConfig.STR),
                                 ('password_field',
                                  'password', PluginConfig.STR),
                                 (
                                     'data_format', '%u=%U&%p=%P&fixed_value=366951344defc44d40d10b73ce711f85',
                                  PluginConfig.STR),
                                 ('auth_url', URL(base_url +
                                  'auth.php'), PluginConfig.URL),
                                 ('method', 'POST', PluginConfig.STR),
                                 ('check_url', URL(base_url +
                                  'home.php'), PluginConfig.URL),
                                 ('check_string', '<title>Home page</title>',
                                  PluginConfig.STR),
                                  ),
                         ),
        }
    }

    def test_post_auth_xss(self):
        self._scan(self._run_config['target'], self._run_config['plugins'])

        vulns = self.kb.get('xss', 'xss')

        self.assertEquals(len(vulns), 1, vulns)

        vuln = vulns[0]
        self.assertEquals(vuln.get_name(),
                          'Cross site scripting vulnerability')
        self.assertEquals(vuln.get_var(), 'section')
