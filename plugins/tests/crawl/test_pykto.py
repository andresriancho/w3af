# -*- coding: utf-8 -*-
'''
test_pykto.py

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
import unittest
import re

from plugins.tests.helper import PluginTest, PluginConfig
from plugins.crawl.pykto import NiktoTestParser, IsVulnerableHelper, Config

from core.data.parsers.url import URL
from core.data.dc.headers import Headers
from core.data.misc.file_utils import days_since_file_update
from core.data.url.HTTPResponse import HTTPResponse


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
        self.assertGreater(len(vulns), 5, vulns)

        urls = self.kb.get_all_known_urls()
        self.assertTrue(len(urls) > 5, urls)

        hidden_url = 'http://moth/hidden/'
        self.assertIn(hidden_url, [u.url_string for u in urls])
        
        expected = ['http://moth/images/', 'http://moth/phpinfo.php',
                    'http://moth/hidden/', 'http://moth/sitemap.xml', 
                    'http://moth/.svn/entries', 'http://moth/server-status',
                    'http://moth/_vti_inf.html', 'http://moth/icons/README',
                    'http://moth/setup/', 'http://moth/reports/rwservlet/showenv',
                    'http://moth/reports/', 'http://moth/index.php']
        self.assertEqual(set(expected),
                         set([v.get_url().url_string for v in vulns]))
        

class TestIsVulnerableHelper(unittest.TestCase):
    # is_vuln = IsVulnerableHelper(match_1, match_1_or, match_1_and, fail_1, fail_2)
    
    def test_checks_only_response_code_case01(self):
        is_vuln = IsVulnerableHelper(200, None, None, None, None)
        self.assertTrue( is_vuln.checks_only_response_code() )
    
    def test_checks_only_response_code_case02(self):
        is_vuln = IsVulnerableHelper(200, 302, None, None, None)
        self.assertTrue( is_vuln.checks_only_response_code() )

    def test_checks_only_response_code_case03(self):
        is_vuln = IsVulnerableHelper(200, re.compile('a'), None, None, None)
        self.assertFalse( is_vuln.checks_only_response_code() )

    def test_checks_only_response_code_case04(self):
        is_vuln = IsVulnerableHelper(re.compile('a'), re.compile('b'),
                                     None, None, None)
        self.assertFalse( is_vuln.checks_only_response_code() )

    def test_check_case01(self):
        is_vuln = IsVulnerableHelper(re.compile('abc'), None, None, None, None)
        url = URL('http://moth/')
        http_response = HTTPResponse(200, 'hello world abc def', Headers(),
                                     url, url)
        self.assertTrue( is_vuln.check(http_response) )

    def test_check_case02(self):
        is_vuln = IsVulnerableHelper(re.compile('xyz'), None, None, None, None)
        url = URL('http://moth/')
        http_response = HTTPResponse(200, 'hello world abc def', Headers(),
                                     url, url)
        self.assertFalse( is_vuln.check(http_response) )

    def test_check_case03(self):
        is_vuln = IsVulnerableHelper(re.compile('xyz'), re.compile('def'),
                                     None, None, None)
        url = URL('http://moth/')
        http_response = HTTPResponse(200, 'hello world abc def', Headers(),
                                     url, url)
        self.assertTrue( is_vuln.check(http_response) )

    def test_check_case04(self):
        is_vuln = IsVulnerableHelper(200, re.compile('def'),
                                     None, None, None)
        url = URL('http://moth/')
        http_response = HTTPResponse(200, 'hello world abc def', Headers(),
                                     url, url)
        self.assertTrue( is_vuln.check(http_response) )

    def test_check_case05(self):
        is_vuln = IsVulnerableHelper(200, 301, None, None, None)
        url = URL('http://moth/')
        http_response = HTTPResponse(301, 'hello world abc def', Headers(),
                                     url, url)
        self.assertTrue( is_vuln.check(http_response) )

    def test_check_case06(self):
        is_vuln = IsVulnerableHelper(200, 301, re.compile('hello'), None, None)
        url = URL('http://moth/')
        http_response = HTTPResponse(301, 'hello world abc def', Headers(),
                                     url, url)
        self.assertTrue( is_vuln.check(http_response) )

    def test_check_case07(self):
        is_vuln = IsVulnerableHelper(200, 301, re.compile('xyz'), None, None)
        url = URL('http://moth/')
        http_response = HTTPResponse(301, 'hello world abc def', Headers(),
                                     url, url)
        self.assertFalse( is_vuln.check(http_response) )

    def test_check_case08(self):
        is_vuln = IsVulnerableHelper(200, 301, re.compile('def'),
                                     re.compile('xyz'), re.compile('abc'))
        url = URL('http://moth/')
        http_response = HTTPResponse(301, 'hello world abc def', Headers(),
                                     url, url)
        self.assertFalse( is_vuln.check(http_response) )

    def test_check_case09(self):
        is_vuln = IsVulnerableHelper(200, 301, re.compile('def'),
                                     re.compile('xyz'), re.compile('spam'))
        url = URL('http://moth/')
        http_response = HTTPResponse(301, 'hello world abc def', Headers(),
                                     url, url)
        self.assertTrue( is_vuln.check(http_response) )
        
class TestNiktoTestParser(PluginTest):
    def test_updated_scan_db(self):
        pykto_inst = self.w3afcore.plugins.get_plugin_inst('crawl', 'pykto')

        scan_db_file = pykto_inst.DB_FILE
        is_older = days_since_file_update(scan_db_file, 30)

        msg = 'The scan database file is too old. The following commands need'\
              ' to be run in order to update it:\n'\
              'cd plugins/crawl/pykto/\n'\
              'python update_scan_db.py\n'\
              'git commit -m "Updating scan_database.db file." scan_database.db\n'\
              'git push\n'\
              'cd -'
        self.assertFalse(is_older, msg)
    
    def test_not_too_many_ignores(self):
        config = Config(['/cgi-bin/'],[],[],[],[])
        url = URL('http://moth/')
        pykto_inst = self.w3afcore.plugins.get_plugin_inst('crawl', 'pykto')
        nikto_parser = NiktoTestParser(pykto_inst.DB_FILE, config, url)
        
        # Go through all the lines        
        generator = nikto_parser.test_generator()
        [i for (i,) in generator]
        
        self.assertLess(len(nikto_parser.ignored), 30, len(nikto_parser.ignored))
    
    def test_parse_db_line_basic(self):
        '''
        This test reads a line from the DB and parses it, it's objective is to
        make sure that DB upgrades with update_scan_db.py do not break the code
        at pykto.py.
        '''
        config = Config(['/cgi-bin/'],[],[],[],[])
        url = URL('http://moth/')
        pykto_inst = self.w3afcore.plugins.get_plugin_inst('crawl', 'pykto')
        nikto_parser = NiktoTestParser(pykto_inst.DB_FILE, config, url)
        
        line = u'"000003","0","1234576890ab","@CGIDIRScart32.exe","GET","200"'\
                ',"","","","","request cart32.exe/cart32clientlist","",""'
        nikto_tests = [i for i in nikto_parser._parse_db_line(line)]
        
        self.assertEqual(len(nikto_tests), 1)
        
        nikto_test = nikto_tests[0]
    
        self.assertEqual(nikto_test.id, '000003')
        self.assertEqual(nikto_test.osvdb, '0')
        self.assertEqual(nikto_test.tune, '1234576890ab')
        self.assertEqual(nikto_test.uri.url_string, 'http://moth/cgi-bin/cart32.exe')
        self.assertEqual(nikto_test.method, 'GET')
        self.assertEqual(nikto_test.match_1, 200)
        self.assertEqual(nikto_test.match_1_or, None)
        self.assertEqual(nikto_test.match_1_and, None)
        self.assertEqual(nikto_test.fail_1, None)
        self.assertEqual(nikto_test.fail_2, None)
        self.assertEqual(nikto_test.message, 'request cart32.exe/cart32clientlist')
        self.assertEqual(nikto_test.data, '')
        self.assertEqual(nikto_test.headers, '')
        
        generator = nikto_parser.test_generator()
        cart32_test_from_db = [i for (i,) in generator if i.id == '000003'][0]
        
        self.assertEqual(cart32_test_from_db.uri, nikto_test.uri)
        self.assertEqual(cart32_test_from_db.match_1, nikto_test.match_1)        
        self.assertEqual(cart32_test_from_db.message, nikto_test.message)

    def test_parse_db_line_junk(self):
        config = Config(['/cgi-bin/'],[],[],[],[])
        url = URL('http://moth/')
        pykto_inst = self.w3afcore.plugins.get_plugin_inst('crawl', 'pykto')
        nikto_parser = NiktoTestParser(pykto_inst.DB_FILE, config, url)
        
        line = u'"0","0","","/docs/JUNK(5)","GET","200"'\
                ',"","","","","","",""'
        nikto_tests = [i for i in nikto_parser._parse_db_line(line)]
        
        self.assertEqual(len(nikto_tests), 1)
        
        nikto_test = nikto_tests[0]
    
        self.assertIn('/docs/', nikto_test.uri.url_string)
        self.assertEqual(len('/docs/') + 5, len(nikto_test.uri.get_path()))

    def test_parse_db_line_no_vars(self):
        config = Config([],[],[],[],[])
        url = URL('http://moth/')
        pykto_inst = self.w3afcore.plugins.get_plugin_inst('crawl', 'pykto')
        nikto_parser = NiktoTestParser(pykto_inst.DB_FILE, config, url)
        
        line = u'"0","0","","/docs/","GET","200"'\
                ',"","","","","","",""'
        nikto_tests = [i for i in nikto_parser._parse_db_line(line)]
        
        self.assertEqual(len(nikto_tests), 1)
        
        nikto_test = nikto_tests[0]
    
        self.assertEqual('/docs/', nikto_test.uri.get_path())

    def test_parse_db_line_cgidirs(self):
        config = Config(['/cgi-bin/'],[],[],[],[])
        url = URL('http://moth/')
        pykto_inst = self.w3afcore.plugins.get_plugin_inst('crawl', 'pykto')
        nikto_parser = NiktoTestParser(pykto_inst.DB_FILE, config, url)
        
        line = u'"0","0","","@CGIDIRS","GET","200"'\
                ',"","","","","","",""'
        nikto_tests = [i for i in nikto_parser._parse_db_line(line)]
        
        self.assertEqual(len(nikto_tests), 1)
        
        nikto_test = nikto_tests[0]
    
        self.assertEqual('/cgi-bin/', nikto_test.uri.get_path())
        
    def test_parse_db_line_admin_dirs(self):
        admin_dirs = ['/adm/', '/admin/']
        
        config = Config(['/cgi-bin/'],admin_dirs,[],[],[])
        url = URL('http://moth/')
        pykto_inst = self.w3afcore.plugins.get_plugin_inst('crawl', 'pykto')
        nikto_parser = NiktoTestParser(pykto_inst.DB_FILE, config, url)
        
        line = u'"0","0","","@ADMIN","GET","200"'\
                ',"","","","","","",""'
        nikto_tests = [i for i in nikto_parser._parse_db_line(line)]
        
        self.assertEqual(len(nikto_tests), 2)
        
        self.assertEqual(admin_dirs,
                         [nt.uri.get_path() for nt in nikto_tests])
        

    def test_parse_db_line_admin_users_two(self):
        admin_dirs = ['/adm/', '/admin/']
        users = ['sys', 'root']
        
        config = Config([],admin_dirs,[],[],users)
        url = URL('http://moth/')
        pykto_inst = self.w3afcore.plugins.get_plugin_inst('crawl', 'pykto')
        nikto_parser = NiktoTestParser(pykto_inst.DB_FILE, config, url)
        
        line = u'"0","0","","@ADMIN@USERS","GET","200"'\
                ',"","","","","","",""'
        nikto_tests = [i for i in nikto_parser._parse_db_line(line)]
        
        self.assertEqual(len(nikto_tests), 4)
        
        self.assertEqual(['/adm/sys', '/adm/root', '/admin/sys', '/admin/root'],
                         [nt.uri.get_path() for nt in nikto_tests])
        
    def test_parse_db_line_raw_bytes(self):
        config = Config(['/cgi-bin/'],[],[],[],[])
        url = URL('http://moth/')
        pykto_inst = self.w3afcore.plugins.get_plugin_inst('crawl', 'pykto')
        nikto_parser = NiktoTestParser(pykto_inst.DB_FILE, config, url)
        
        line = '"006251","0","1","/administraçao.php","GET","200","","",""'\
               ',"","Admin login page/section found.","",""'
        try:
            [_ for _ in nikto_parser._parse_db_line(line)]
        except TypeError:
            self.assertTrue(True)
        else:
            self.assertTrue(False)
