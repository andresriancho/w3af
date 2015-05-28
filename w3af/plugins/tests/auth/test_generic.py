"""
test_generic.py

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
from nose.plugins.skip import SkipTest
from nose.plugins.attrib import attr

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.extended_urllib import ExtendedUrllib


class TestGeneric(PluginTest):

    base_url = get_moth_http('/auth/auth_1/')
    demo_testfire = 'http://demo.testfire.net/bank/'

    _run_config = {
        'target': base_url,
        'plugins': {
            'crawl': (PluginConfig('web_spider',
                        ('only_forward', True, PluginConfig.BOOL),
                        ('ignore_regex', '.*logout.*', PluginConfig.STR)),),
            'audit': (PluginConfig('xss',),),
            'auth': (PluginConfig('generic',
                                 ('username', 'user@mail.com', PluginConfig.STR),
                                 ('password', 'passw0rd', PluginConfig.STR),
                                 ('username_field',
                                  'username', PluginConfig.STR),
                                 ('password_field',
                                  'password', PluginConfig.STR),
                                 ('auth_url', URL(base_url +
                                  'login_form.py'), PluginConfig.URL),
                                 ('check_url', URL(base_url +
                                  'post_auth_xss.py'), PluginConfig.URL),
                                 ('check_string', 'read your input',
                                  PluginConfig.STR),
                                  ),
                         ),
        }
    }

    demo_testfire_net = {
        'target': demo_testfire,
        'plugins': {
        'crawl': (
        PluginConfig('web_spider',
                     ('only_forward', True, PluginConfig.BOOL),
                     ('ignore_regex',
                      '.*logout.*', PluginConfig.STR),
                     (
        'follow_regex', '.*queryxpath.*', PluginConfig.STR)),

        ),
            'auth': (PluginConfig('generic',
                                 ('username', 'admin', PluginConfig.STR),
                                 ('password', 'admin', PluginConfig.STR),
                                 ('username_field', 'uid', PluginConfig.STR),
                                 ('password_field', 'passw', PluginConfig.STR),
                                 ('auth_url', URL(demo_testfire +
                                  'login.aspx'), PluginConfig.URL),
                                 ('check_url', URL(demo_testfire +
                                  'main.aspx'), PluginConfig.URL),
                                 ('check_string', 'View Recent Transactions',
                                  PluginConfig.STR),
                                  ),
                         ),
        }
    }

    @attr('smoke')
    def test_post_auth_xss(self):
        self._scan(self._run_config['target'], self._run_config['plugins'])

        vulns = self.kb.get('xss', 'xss')

        self.assertEquals(len(vulns), 1, vulns)

        vuln = vulns[0]
        self.assertEquals(vuln.get_name(), 'Cross site scripting vulnerability')
        self.assertEquals(vuln.get_token_name(), 'text')
        self.assertEquals(vuln.get_url().get_path(),
                          '/auth/auth_1/post_auth_xss.py')

    @attr('internet')
    @attr('fails')
    def test_demo_testfire_net(self):
        # We don't control the demo.testfire.net domain, so we'll check if its
        # up before doing anything else
        uri_opener = ExtendedUrllib()
        login_url = URL(self.demo_testfire + 'login.aspx')
        try:
            res = uri_opener.GET(login_url)
        except:
            raise SkipTest('demo.testfire.net is unreachable!')
        else:
            if not 'Online Banking Login' in res.body:
                raise SkipTest('demo.testfire.net has changed!')

        self._scan(self.demo_testfire_net['target'],
                   self.demo_testfire_net['plugins'])

        urls = self.kb.get_all_known_urls()
        url_strings = set(str(u) for u in urls)

        self.assertTrue(self.demo_testfire + 'queryxpath.aspx' in url_strings)
        self.assertTrue(
            self.demo_testfire + 'queryxpath.aspx.cs' in url_strings)