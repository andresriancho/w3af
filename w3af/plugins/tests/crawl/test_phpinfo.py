"""
test_phpinfo.py

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


class TestPHPInfo(PluginTest):

    base_url = 'https://moth/'

    _run_config = {
        'target': base_url,
        'plugins': {'crawl': (PluginConfig('phpinfo'),)}
    }

    @attr('smoke')
    @attr('ci_fails')
    def test_phpinfo(self):
        self._scan(self._run_config['target'], self._run_config['plugins'])

        urls = self.kb.get_all_known_urls()
        urls = [url.url_string for url in urls]

        self.assertTrue(self.base_url + 'phpinfo.php' in urls)

        infos = self.kb.get('phpinfo', 'phpinfo')
        self.assertTrue(len(infos) > 5, infos)

        EXPECTED_INFOS = set([
            'PHP register_globals: Off',
            'PHP expose_php: On',
            'PHP session.hash_function:md5',
            'phpinfo() file found'])

        info_urls = [i.get_url().url_string for i in infos]
        self.assertIn(self.base_url + 'phpinfo.php', info_urls)
        
        found_infos = set([i.get_name() for i in infos])
        
        self.assertTrue(found_infos.issuperset(EXPECTED_INFOS))