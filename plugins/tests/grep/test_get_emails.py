'''
test_get_emails.py

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


class TestGetEmails(PluginTest):
    
    get_emails_url = 'https://moth/w3af/grep/get_emails/'
    
    _run_configs = {
        'cfg1': {
            'target': get_emails_url,
            'plugins': {
                'grep': (PluginConfig('get_emails',
                                      ('onlyTargetDomain', False, PluginConfig.BOOL)),),
                'discovery': (
                    PluginConfig('web_spider',
                                 ('onlyForward', True, PluginConfig.BOOL)),
                )         
                
            }
        }
    }
    
    def test_found_emails(self):
        cfg = self._run_configs['cfg1']
        self._scan(cfg['target'], cfg['plugins'])
        
        target_emails = self.kb.getData('emails', 'emails')
        self.assertEqual( len(target_emails), 0)
        
        all_email_infos = self.kb.getData('emails', 'external_emails')
        all_emails = set([ i['mail'] for i in all_email_infos ])
        
        EXPECTED = set([u'f00@moth.com', u'bar@moth.com', u'hello@world.com',
                        u'world@f00.net', u'planer@moth.com', u'pp@moth.com',
                        u'notme@gmail.com'])
        
        self.assertEqual( all_emails, EXPECTED)
        