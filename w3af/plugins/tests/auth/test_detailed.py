"""
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
"""
from nose.plugins.attrib import attr
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.data.parsers.url import URL
from w3af.core.controllers.ci.moth import get_moth_http


class TestDetailed(PluginTest):

    target_url = get_moth_http('/auth/detailed/')
    
    auth_url = URL(target_url + 'auth.py')
    check_url = URL(target_url + 'home.py')
    check_string = '<title>Home page</title>'
    data_format = '%u=%U&%p=%P&fixed_value=366951344defc44d40d10b73ce711f85'
    
    _run_config = {
        'target': target_url,
        'plugins': {
        'crawl': (
        PluginConfig('web_spider',
                     ('only_forward', True, PluginConfig.BOOL),
                     ('ignore_regex', '.*logout.*', PluginConfig.STR)),

        ),
            'audit': (PluginConfig('xss',),),
            'auth': (PluginConfig('detailed',
                                 ('username', 'admin', PluginConfig.STR),
                                 ('password', 'nimda', PluginConfig.STR),
                                 ('username_field', 'username', PluginConfig.STR),
                                 ('password_field', 'password', PluginConfig.STR),
                                 ('data_format', data_format, PluginConfig.STR),
                                 ('auth_url', auth_url, PluginConfig.URL),
                                 ('method', 'POST', PluginConfig.STR),
                                 ('check_url', check_url, PluginConfig.URL),
                                 ('check_string', check_string, PluginConfig.STR),
                                  ),
                         ),
        }
    }

    @attr('ci_fails')
    def test_post_auth_xss(self):
        self._scan(self._run_config['target'], self._run_config['plugins'])

        vulns = self.kb.get('xss', 'xss')

        self.assertEquals(len(vulns), 1, vulns)

        vuln = vulns[0]
        self.assertEquals(vuln.get_name(),
                          'Cross site scripting vulnerability')
        self.assertEquals(vuln.get_var(), 'section')