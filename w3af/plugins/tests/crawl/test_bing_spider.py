"""
test_bing_spider.py

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

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


@attr('fails')
class TestBingSpider(PluginTest):

    target_url = 'http://www.bonsai-sec.com/'
    target_url_fmt = 'http://www.bonsai-sec.com/%s'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'crawl': (PluginConfig('bing_spider'),)}
        }
    }
    EXPECTED_URLS = (
        'es/education/', 'en/clients/', 'es/', 'services/',
        'research/', 'blog/', 'education/', 'es/research/',
        'blog', 'es/clients/', '',
    )

    MOCK_RESPONSES = [MockResponse(target_url_fmt % eu, 'Response body.') for eu in EXPECTED_URLS]

    def test_found_urls(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        urls = self.kb.get_all_known_urls()

        found_urls = set(str(u) for u in urls),
        expected_urls = set((self.target_url + end) for end in self.EXPECTED_URLS)
        
        self.assertEquals(found_urls, expected_urls)
