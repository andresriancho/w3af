'''
test_pykto.py

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
from core.data.misc.file_utils import days_since_file_update


class TestPykto(PluginTest):

    base_url = 'http://moth/w3af/'

    _run_configs = {
        'cfg': {
            'target': base_url,
            'plugins': {'crawl': (PluginConfig('pykto'),)}
        }
    }

    def test_basic_pykto(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        vulns = self.kb.get('pykto', 'vuln')

        self.assertTrue(len(vulns) > 10, vulns)

        urls = self.kb.get('urls', 'url_objects')
        self.assertTrue(len(urls) > 5, urls)

        hidden_url = 'http://moth/hidden/'

        for url in urls:
            if url.url_string == hidden_url:
                self.assertTrue(True)
                break
        else:
            self.assertTrue(False)

    def test_updated_scan_db(self):
        pykto_inst = self.w3afcore.plugins.get_plugin_inst('crawl', 'pykto')

        scan_db_file = pykto_inst._db_file
        is_older = days_since_file_update(scan_db_file, 30)

        msg = 'The scan database file is too old. The following commands need'\
              ' to be run in order to update it:\n'\
              'cd plugins/crawl/pykto/\n'\
              'python update_scan_db.py\n'\
              'svn commit -m "Updating scan_database.db file." scan_database.db\n'\
              'cd -'
        self.assertFalse(is_older, msg)
    
    def test_parse_db_line_basic(self):
        pykto_inst = self.w3afcore.plugins.get_plugin_inst('crawl', 'pykto')
        
        line = '"apache","/docs/","200","GET","Description"'
        test_generator = pykto_inst._parse_db_line(line)
        
        tests = [i for i in test_generator]
        self.assertEqual(len(tests), 1)
        self.assertEqual([('apache', '/docs/', '200', 'GET', 'Description')], tests)

    def test_parse_db_line_junk(self):
        pykto_inst = self.w3afcore.plugins.get_plugin_inst('crawl', 'pykto')
        
        line = '"apache","/docs/JUNK(5)","200","GET","Description"'
        test_generator = pykto_inst._parse_db_line(line)
        
        tests = [i for i in test_generator]
        self.assertEqual(len(tests), 1)
        
        server, query, expected_response, method , desc = tests[0]
        self.assertTrue(query.startswith('/docs/'))
        self.assertEqual(len(query), len('/docs/') + 5)

    def test_parse_db_line_cgidirs(self):
        pykto_inst = self.w3afcore.plugins.get_plugin_inst('crawl', 'pykto')
        
        line = '"apache","@CGIDIRS","200","GET","CGI"'
        test_generator = pykto_inst._parse_db_line(line)
        
        tests = [i for i in test_generator]
        self.assertEqual(len(tests), 1)
        self.assertEqual([('apache', '/cgi-bin/', '200', 'GET', 'CGI')], tests)
        
    def test_parse_db_line_admin_dirs(self):
        pykto_inst = self.w3afcore.plugins.get_plugin_inst('crawl', 'pykto')
        
        line = '"apache","@ADMINDIRS","200","GET","CGI"'
        test_generator = pykto_inst._parse_db_line(line)
        
        tests = [i for i in test_generator]
        self.assertEqual(len(tests), 2)
        self.assertEqual([('apache', '/admin/', '200', 'GET', 'CGI'),
                          ('apache', '/adm/', '200', 'GET', 'CGI')], tests)
        

    def test_parse_db_line_admin_users_two(self):
        pykto_inst = self.w3afcore.plugins.get_plugin_inst('crawl', 'pykto')
        
        line = '"apache","@ADMINDIRS@USERS","200","GET","CGI"'
        test_generator = pykto_inst._parse_db_line(line)
        
        tests = [i for i in test_generator]
        self.assertIn(('apache', '/adm/sys', '200', 'GET', 'CGI'), tests)
        self.assertIn(('apache', '/admin/bin', '200', 'GET', 'CGI'), tests)
    
