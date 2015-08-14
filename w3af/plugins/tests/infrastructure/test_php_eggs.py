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
from mock import patch

from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


@attr('smoke')
class TestPHPEggs(PluginTest):

    target_url = 'http://mock/'
    MOCK_RESPONSES = [MockResponse('http://mock/?=PHPB8B5F2A0-3C92-11d3-A3A9-4C7B08C10000',
                                   '1'),
                      MockResponse('http://mock/?=PHPE9568F34-D428-11d2-A769-00AA001ACF42',
                                   '2', content_type='image/png'),
                      MockResponse('http://mock/?=PHPE9568F35-D428-11d2-A769-00AA001ACF42',
                                   '3', content_type='image/png'),
                      MockResponse('http://mock/?=PHPE9568F36-D428-11d2-A769-00AA001ACF42',
                                   '4', content_type='image/png')]

    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {'infrastructure': (PluginConfig('php_eggs'),)}
        }
    }

    def test_php_eggs_fingerprinted(self):
        cfg = self._run_configs['cfg']

        with patch('w3af.plugins.infrastructure.php_eggs.md5_hash') as md5mock:
            def side_effect(body):
                return {'1': 'a4c057b11fa0fba98c8e26cd7bb762a8',
                        '2': 'c48b07899917dfb5d591032007041ae3',
                        '3': 'fb3bbd9ccc4b3d9e0b3be89c5ff98a14',
                        '4': '7675f1d01c927f9e6a4752cf182345a2'}.get(body)
            md5mock.side_effect = side_effect
            self._scan(self.target_url, cfg['plugins'])

        eggs = self.kb.get('php_eggs', 'eggs')
        self.assertEqual(len(eggs), 4, eggs)

        for egg in eggs:
            self.assertIn('PHP Egg', egg.get_name())

        php_version = self.kb.get('php_eggs', 'version')
        self.assertEqual(len(php_version), 1, php_version)

        php_version = php_version[0]
        self.assertEqual(php_version['version'], [u'5.3.2', u'5.3.1'])


@attr('smoke')
class TestPHPEggsNoFingerprint(PluginTest):

    target_url = 'http://mock/'
    MOCK_RESPONSES = [MockResponse(target_url, 'Index is not empty')]

    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {'infrastructure': (PluginConfig('php_eggs'),)}
        }
    }

    def test_php_eggs_fingerprinted(self):
        cfg = self._run_configs['cfg']

        self._scan(self.target_url, cfg['plugins'])

        eggs = self.kb.get('php_eggs', 'eggs')
        php_version = self.kb.get('php_eggs', 'version')

        self.assertEqual(len(eggs), 0, eggs)
        self.assertEqual(len(php_version), 0, php_version)
