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

from ..helper import PluginTest, PluginConfig

class TestXSS(PluginTest):
    
    xss_url = 'http://moth/w3af/audit/xss/'
    xss_302_url = 'http://moth/w3af/audit/xss/302/'
    
    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': (
                PluginConfig(
                     'audit.xss',
                     ('checkStored', True, PluginConfig.BOOL),
                     ('numberOfChecks', 3, PluginConfig.INT)),
                PluginConfig(
                     'discovery.webSpider',
                     ('onlyForward', True, PluginConfig.BOOL))
                ),
            }
        }
    
    def test_found_xss(self):
        cfg = self._run_configs['cfg']
        self._scan(self.xss_url, cfg['plugins'])
        xssvulns = self.kb.getData('xss', 'xss')
        expected = [
            ('simple_xss_no_script_2.php', 'text', set(['text'])),
            ('dataReceptor.php', 'firstname', set(['user', 'firstname'])),
            ('simple_xss_no_script.php', 'text', set(['text'])),
            ('simple_xss_no_js.php', 'text', set(['text'])),
            ('simple_xss_no_quotes.php', 'text', set(['text'])),
            ('dataReceptor3.php', 'user', set(['user', 'pass'])),
            ('simple_xss.php', 'text', set(['text'])),
            ('no_tag_xss.php', 'text', set(['text'])),
            ('dataReceptor2.php', 'empresa', set(['empresa', 'firstname'])),
            ('stored/writer.php', 'a', set(['a'])),
        ]
        res = [(str(m.getURL()), m.getVar(), set(m.getDc().keys()))
                for m in (xv.getMutant() for xv in xssvulns)]
        self.assertEquals(
            sorted([(self.xss_url + e[0], e[1], e[2]) for e in expected],
                    key=lambda r: r[0] + r[1]),
            sorted(res, key=lambda r: r[0] + r[1]),
        )
        
    def test_found_xss_with_redirect(self):
        cfg = self._run_configs['cfg']
        self._scan(self.xss_302_url, cfg['plugins'])
        xssvulns = self.kb.getData('xss', 'xss')
        expected = [
            ('302.php', 'x', set(['x'])),
            ('302.php', 'a', set(['a'])),
            ('printer.php', 'a', set(['a', 'added'])),
            ('printer.php', 'added', set(['a', 'added'])),
            ('printer.php', 'added', set(['added'])),
            ('printer.php', 'x', set(['x', 'added'])),
            ('printer.php', 'added', set(['x', 'added']))
        ]
        res = [(str(m.getURL()), m.getVar(), set(m.getDc().keys()))
                        for m in (xv.getMutant() for xv in xssvulns)]
        
        self.assertEquals(
            sorted([(self.xss_302_url + e[0], e[1], e[2]) for e in expected],
                    key=lambda r: r[0] + r[1]),
            sorted(res, key=lambda r: r[0] + r[1]),
        )