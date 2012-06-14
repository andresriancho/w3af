'''
test_netcraft.py

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

class TestNetcraft(PluginTest):
    
    base_url = 'http://www.w3af.org/'
    
    _run_configs = {
        'cfg1': {
            'target': base_url,
            'plugins': {'discovery': (PluginConfig('netcraft'),)}
            }
        }
    
    def test_fuzzer_found_urls(self):
        cfg = self._run_configs['cfg1']
        self._scan(cfg['target'], cfg['plugins'])
        expected_infos = ( ('netblock_owner', 'Netblock owner', u'Netcraft reports that the netblock owner for the target domain is GoDaddy.com, LLC') ,
                         )

        for kb_item, ename, edesc in expected_infos:
            items = self.kb.getData('netcraft', kb_item)

            self.assertEquals( len(items), 1)

            iname = items[0].getName()
            idesc = items[0].getDesc()

            self.assertEquals( iname, ename )
            self.assertTrue( idesc.startswith(edesc) )

