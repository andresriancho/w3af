'''
test_xss.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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
from nose.plugins.attrib import attr

from plugins.tests.helper import PluginTest, PluginConfig


class TestXSS(PluginTest):

    xss_url = 'http://moth/w3af/audit/xss/'
    xss_302_url = 'http://moth/w3af/audit/xss/302/'
    xss_smoke = 'http://moth/w3af/audit/xss/simple_xss_no_js.php'

    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {
                'audit': (
                    PluginConfig(
                        'xss',
                         ('checkStored', True, PluginConfig.BOOL),
                         ('numberOfChecks', 3, PluginConfig.INT)),
                ),
                'crawl': (
                    PluginConfig(
                        'web_spider',
                        ('onlyForward', True, PluginConfig.BOOL)),
                )
            },
        },

        'smoke': {
            'target': xss_smoke + '?text=1',
            'plugins': {
                'audit': (
                    PluginConfig(
                        'xss',
                         ('checkStored', True, PluginConfig.BOOL),
                         ('numberOfChecks', 10, PluginConfig.INT)),
                ),
            },
        }

    }

    @attr('smoke')
    def test_find_one_xss(self):
        cfg = self._run_configs['smoke']
        self._scan(cfg['target'], cfg['plugins'])

        xssvulns = self.kb.get('xss', 'xss')
        kb_data = [(str(m.get_url()), m.get_var(), tuple(sorted(m.get_dc().keys())))
                   for m in (xv.get_mutant() for xv in xssvulns)]

        EXPECTED = [('simple_xss_no_js.php', 'text', ['text']), ]
        expected_data = [(self.xss_smoke, e[1], tuple(sorted(e[2]))
                          ) for e in EXPECTED]

        self.assertEquals(
            set(expected_data),
            set(kb_data),
        )

    def test_found_xss(self):
        cfg = self._run_configs['cfg']
        self._scan(self.xss_url, cfg['plugins'])
        xssvulns = self.kb.get('xss', 'xss')
        expected = [
            ('simple_xss_no_script_2.php', 'text', ['text']),
            ('dataReceptor.php', 'firstname', ['user', 'firstname']),
            ('simple_xss_no_script.php', 'text', ['text']),
            ('simple_xss_no_js.php', 'text', ['text']),
            ('simple_xss_no_quotes.php', 'text', ['text']),
            ('dataReceptor3.php', 'user', ['user', 'pass']),
            ('simple_xss.php', 'text', ['text']),
            ('no_tag_xss.php', 'text', ['text']),
            ('dataReceptor2.php', 'empresa', ['empresa', 'firstname']),
            ('stored/writer.php', 'a', ['a']),
            ('xss_clean.php', 'text', ['text', ]),
            ('xss_clean_4_strict.php', 'text', ['text', ])

        ]
        res = [(str(m.get_url()), m.get_var(), tuple(sorted(m.get_dc().keys())))
               for m in (xv.get_mutant() for xv in xssvulns)]
        self.assertEquals(
            set([(self.xss_url + e[0], e[1], tuple(sorted(e[2])
                                                   )) for e in expected]),
            set(res),
        )

    def test_found_xss_with_redirect(self):
        cfg = self._run_configs['cfg']
        self._scan(self.xss_302_url, cfg['plugins'])
        xssvulns = self.kb.get('xss', 'xss')
        expected = [
            ('302.php', 'x', ('x',)),
            ('302.php', 'a', ('a',)),
            ('printer.php', 'a', ('a', 'added',)),
            ('printer.php', 'added', ('a', 'added',)),
            ('printer.php', 'added', ('added',)),
            ('printer.php', 'x', ('x', 'added')),
            ('printer.php', 'added', ('x', 'added'))
        ]
        res = [(str(m.get_url()), m.get_var(), tuple(sorted(m.get_dc().keys())))
               for m in (xv.get_mutant() for xv in xssvulns)]
        self.assertEquals(
            set([(self.xss_302_url + e[0], e[1], tuple(sorted(
                e[2]))) for e in expected]),
            set(res),
        )
