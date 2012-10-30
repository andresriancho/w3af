'''
test_find_dvcs.py

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
from plugins.tests.helper import PluginTest, PluginConfig
from plugins.crawl.find_dvcs import find_dvcs


class TestFindDVCS(PluginTest):
    
    base_url = 'http://moth/w3af/crawl/find_dvcs/'
    
    _run_configs = {
        'cfg': {
            'target': base_url,
            'plugins': {'crawl': (PluginConfig('find_dvcs'),
                                  PluginConfig('web_spider',
                                         ('onlyForward', True, PluginConfig.BOOL)),)}
            }
        }
    
    def test_dvcs(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        
        vulns_git = self.kb.get('find_dvcs', 'GIT')
        vulns_bzr = self.kb.get('find_dvcs', 'BZR')
        vulns_hg = self.kb.get('find_dvcs', 'HG')
        
        self.assertEqual( len(vulns_git), 1, vulns_git )
        self.assertEqual( len(vulns_bzr), 1, vulns_bzr )
        self.assertEqual( len(vulns_hg), 1, vulns_hg )
        
        self.assertEquals( vulns_git[0].getName(), 'Possible git repository found' )
        self.assertEquals( vulns_bzr[0].getName(), 'Possible bzr repository found' )
        self.assertEquals( vulns_hg[0].getName(), 'Possible hg repository found' )


    def test_ignore_file_blank(self):
        fdvcs = find_dvcs()
        files = fdvcs.ignore_file('')
        
        self.assertEqual(files, set())

    def test_ignore_file_two_files_comment(self):
        fdvcs = find_dvcs()
        content = '''# Ignore these files
        foo.txt
        bar*
        spam.eggs
        '''
        files = fdvcs.ignore_file(content)
        
        self.assertEqual(files, set(['foo.txt', 'spam.eggs']))
    
    def test_svn_entries(self):
        '''
        Is the svn_entries function returning garbage? In my workstation the
        function returns '12' which is the content in the file; but no file
        named '12' really exists, so it makes no sense for the parsing function
        to return it.
        '''
        fdvcs = find_dvcs()
        svn_entries = file('.svn/entries').read()
        files = fdvcs.ignore_file(svn_entries)
        self.assertEqual(files, set())
    
    