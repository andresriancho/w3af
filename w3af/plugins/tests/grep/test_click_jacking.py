"""
test_click_jacking.py

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
import w3af.core.data.constants.severity as severity

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


class TestClickJackingVuln(PluginTest):

    target_url = 'http://httpretty'

    MOCK_RESPONSES = [MockResponse('http://httpretty/',
                                   body='Hello world',
                                   method='GET',
                                   status=200)]

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('click_jacking'),),
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL)),
                )

            }
        }
    }

    def test_found_vuln(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        vulns = self.kb.get('click_jacking', 'click_jacking')

        self.assertEquals(1, len(vulns))

        v = vulns[0]
        self.assertEquals(severity.MEDIUM, v.get_severity())
        self.assertEquals('Click-Jacking vulnerability', v.get_name())
        self.assertEquals(len(v.get_id()), 1, v.get_id())
        self.assertIn('The application has no protection', v.get_desc())


class TestClickJackingProtectedXFrameOptions(PluginTest):

    target_url = 'http://httpretty'

    MOCK_RESPONSES = [MockResponse('http://httpretty/',
                                   body='Hello world',
                                   method='GET',
                                   headers={'x-frame-options': 'deny'},
                                   status=200)]

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('click_jacking'),),
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL)),
                )

            }
        }
    }

    def test_no_vuln(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        vulns = self.kb.get('click_jacking', 'click_jacking')

        self.assertEquals(0, len(vulns))


class TestClickJackingCSPNone(PluginTest):

    target_url = 'http://httpretty'

    MOCK_RESPONSES = [MockResponse('http://httpretty/',
                                   body='Hello world',
                                   method='GET',
                                   headers={'Content-Security-Policy': "frame-ancestors 'none';"},
                                   status=200)]

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('click_jacking'),),
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL)),
                )

            }
        }
    }

    def test_no_vuln(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        vulns = self.kb.get('click_jacking', 'click_jacking')

        self.assertEquals(0, len(vulns))


class TestClickJackingCSPWildcard(PluginTest):

    target_url = 'http://httpretty'

    MOCK_RESPONSES = [MockResponse('http://httpretty/',
                                   body='Hello world',
                                   method='GET',
                                   headers={'Content-Security-Policy': "frame-ancestors '*';"},
                                   status=200)]

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('click_jacking'),),
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL)),
                )

            }
        }
    }

    def test_vuln(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        vulns = self.kb.get('click_jacking', 'click_jacking')

        self.assertEquals(1, len(vulns))


class TestClickJackingCSPSpecificDomain(PluginTest):

    target_url = 'http://httpretty'

    MOCK_RESPONSES = [MockResponse('http://httpretty/',
                                   body='Hello world',
                                   method='GET',
                                   headers={'Content-Security-Policy': "frame-ancestors 'somesite.com';"},
                                   status=200)]

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('click_jacking'),),
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL)),
                )

            }
        }
    }

    def test_vuln(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        vulns = self.kb.get('click_jacking', 'click_jacking')

        self.assertEquals(0, len(vulns))


class TestClickJackingCSPSelf(PluginTest):

    target_url = 'http://httpretty'

    MOCK_RESPONSES = [MockResponse('http://httpretty/',
                                   body='Hello world',
                                   method='GET',
                                   headers={'Content-Security-Policy': "frame-ancestors 'self';"},
                                   status=200)]

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('click_jacking'),),
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL)),
                )

            }
        }
    }

    def test_vuln(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        vulns = self.kb.get('click_jacking', 'click_jacking')

        self.assertEquals(0, len(vulns))


class TestClickJackingCSPSelfAndSpecificDomain(PluginTest):

    target_url = 'http://httpretty'

    MOCK_RESPONSES = [MockResponse('http://httpretty/',
                                   body='Hello world',
                                   method='GET',
                                   headers={'Content-Security-Policy': "frame-ancestors self 'somesite.com';"},
                                   status=200)]

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'grep': (PluginConfig('click_jacking'),),
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL)),
                )

            }
        }
    }

    def test_vuln(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        vulns = self.kb.get('click_jacking', 'click_jacking')

        self.assertEquals(0, len(vulns))
