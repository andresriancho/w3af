'''
test_afd.py

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


class TestAFD(PluginTest):

    modsecurity_https_url = 'https://modsecurity/'
    modsecurity_http_url = 'http://modsecurity/'
    moth_url = 'http://moth/'

    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {'infrastructure': (PluginConfig('afd'),)}
        }
    }

    def test_afd_found_http(self):
        cfg = self._run_configs['cfg']
        self._scan(self.modsecurity_http_url, cfg['plugins'])

        infos = self.kb.get('afd', 'afd')

        self.assertEqual(len(infos), 1, infos)

        info = infos[0]

        self.assertEqual(info.get_name(), 'Active filter detected')
        values = [u.split('=')[1] for u in info['filtered']]

        expected = [
            '..%2F..%2F..%2F..%2Fetc%2Fpasswd',
            '.%2F..%2F..%2F..%2Fetc%2Fmotd%00html',
            'id%3Buname+-a',
            '%3C%3F+passthru%28%22id%22%29%3B%3F%3E',
            'type%2Bc%3A%5Cwinnt%5Crepair%5Csam._',
            '..%2F..%2FWINNT%2Fsystem32%2Fcmd.exe%3Fdir%2Bc%3A%5C',
            'ps+-aux%3B',
            '..%2F..%2F..%2F..%2Fbin%2Fchgrp+nobody+%2Fetc%2Fshadow%7C',
            'SELECT+TOP+1+name+FROM+sysusers',
            'exec+master..xp_cmdshell+dir',
            'exec+xp_cmdshell+dir'
        ]

        self.assertEqual(set(expected), set(values), values)

    def test_afd_found_https(self):
        cfg = self._run_configs['cfg']
        self._scan(self.modsecurity_https_url, cfg['plugins'])

        infos = self.kb.get('afd', 'afd')

        self.assertEqual(len(infos), 1, infos)

    def test_afd_not_found(self):
        cfg = self._run_configs['cfg']
        self._scan(self.moth_url, cfg['plugins'])

        infos = self.kb.get('afd', 'afd')

        self.assertEqual(len(infos), 0, infos)
