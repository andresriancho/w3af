"""
test_dot_net_errors.py

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
from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


class TestDotNetErrors(PluginTest):

    target_url = 'http://httpretty'

    MOCK_RESPONSES = [MockResponse('http://httpretty/',
                                   body='<a href="sample.aspx">sample</a>',
                                   method='GET',
                                   status=200),
                      MockResponse('http://httpretty/sample.aspx',
                                   body='Hello world',
                                   method='GET',
                                   status=200),
                      MockResponse('http://httpretty/sample~.aspx',
                                   body='<h2> <i>Runtime Error</i> </h2></span>...',
                                   method='GET',
                                   status=200),
                      ]

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'infrastructure': (PluginConfig('dot_net_errors'),),
                        'crawl': (PluginConfig('web_spider',
                                               ('only_forward', True, PluginConfig.BOOL),),)}
        }
    }

    def test_dot_net_errors(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        infos = self.kb.get('dot_net_errors', 'dot_net_errors')

        self.assertEqual(len(infos), 1, infos)

        info = infos[0]

        self.assertEqual(info.get_name(), 'Information disclosure via .NET errors')


class TestDotNetErrorsWithColonInURL(PluginTest):

    target_url = 'http://httpretty'

    MOCK_RESPONSES = [MockResponse('http://httpretty/',
                                   body='<a href="sample%3a.aspx">sample</a>',
                                   method='GET',
                                   status=200),
                      MockResponse('http://httpretty/sample.aspx',
                                   body='Hello world',
                                   method='GET',
                                   status=200),
                      MockResponse('http://httpretty/sample~.aspx',
                                   body='<h2> <i>Runtime Error</i> </h2></span>...',
                                   method='GET',
                                   status=200),
                      ]

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'infrastructure': (PluginConfig('dot_net_errors'),),
                        'crawl': (PluginConfig('web_spider',
                                               ('only_forward', True, PluginConfig.BOOL),),)}
        }
    }

    def test_dot_net_errors_with_colon_in_url(self):
        #
        # This test is here to check that no exceptions are raised in
        # dot_net_errors._generate_urls() while url-joining the filename that
        # contains the colon (sample%3a.aspx above)
        #
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        infos = self.kb.get('dot_net_errors', 'dot_net_errors')
        self.assertEqual(len(infos), 0, infos)
