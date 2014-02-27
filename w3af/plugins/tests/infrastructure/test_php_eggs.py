"""
test_php_eggs.py

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


@attr('smoke')
class TestPHPEggs(PluginTest):

    moth_url = 'http://moth/'

    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {'infrastructure': (PluginConfig('php_eggs'),)}
        }
    }

    @attr('ci_fails')
    def test_php_eggs_fingerprinted(self):
        cfg = self._run_configs['cfg']
        self._scan(self.moth_url, cfg['plugins'])

        eggs = self.kb.get('php_eggs', 'eggs')
        self.assertEqual(len(eggs), 4, eggs)

        for egg in eggs:
            self.assertIn('PHP Egg', egg.get_name())

        php_version = self.kb.get('php_eggs', 'version')
        self.assertEqual(len(php_version), 1, php_version)

        php_version = php_version[0]
        self.assertEqual(php_version['version'], ['5.3.10'])