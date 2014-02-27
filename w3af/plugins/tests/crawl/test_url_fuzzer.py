"""
test_urlfuzzer.py

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


class TestURLFuzzer(PluginTest):

    base_url = 'http://moth/w3af/crawl/url_fuzzer'

    _run_configs = {
        'standalone': {
            'target': base_url + '/index.html',
            'plugins': {'crawl': (PluginConfig('url_fuzzer'),)}
        },
    }

    @attr('ci_fails')
    def test_fuzzer_found_urls(self):
        cfg = self._run_configs['standalone']
        self._scan(cfg['target'], cfg['plugins'])
        
        expected_urls = ('/index.html', '/index.html~',
                         '/index.html.zip', '.tgz')
        urls = self.kb.get_all_known_urls()
        
        self.assertEquals(
            set(str(u) for u in urls),
            set((self.base_url + end) for end in expected_urls)
        )
        