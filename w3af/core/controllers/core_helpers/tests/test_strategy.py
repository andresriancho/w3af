"""
test_strategy.py

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

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig


class TestStrategy(PluginTest):
    target_url = get_moth_http('/audit/sql_injection/'
                               'where_string_single_qs.py?uname=pablo')

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'audit': (PluginConfig('sqli'),),
            }
        }
    }

    @attr('smoke')
    @attr('moth')
    def test_same_fr_set_object(self):
        cfg = self._run_configs['cfg']

        id_before_fr = id(self.kb.get_all_known_fuzzable_requests())
        id_before_ur = id(self.kb.get_all_known_urls())
        
        self._scan(cfg['target'], cfg['plugins'])
        
        id_after_fr = id(self.kb.get_all_known_fuzzable_requests())
        id_after_ur = id(self.kb.get_all_known_urls())

        self.assertEquals(id_before_fr, id_after_fr)
        self.assertEquals(id_before_ur, id_after_ur)