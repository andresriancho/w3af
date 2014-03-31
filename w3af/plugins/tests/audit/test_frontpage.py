"""
test_frontpage.py

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
from nose.plugins.skip import SkipTest

from w3af.plugins.tests.helper import PluginTest, PluginConfig


class TestFrontpage(PluginTest):

    target_vuln_all = 'http://moth/'

    _run_configs = {
        'cfg': {
            'target': None,
            'plugins': {
                'audit': (PluginConfig('frontpage',),),
            }
        },
    }

    @attr('ci_fails')
    def test_no_frontpage(self):
        cfg = self._run_configs['cfg']
        self._scan(self.target_vuln_all, cfg['plugins'])

        vulns = self.kb.get('frontpage', 'frontpage')

        EXPECTED = set()

        self.assertEquals(EXPECTED,
                          set([v.get_name() for v in vulns])
                          )

    @attr('ci_fails')
    def test_frontpage_upload(self):
        msg = 'FIXME: Need to setup a working frontpage environment and have'\
              ' a positive test also!'
        raise SkipTest(msg)