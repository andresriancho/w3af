'''
test_sqlmap_wrapper.py

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
import os
import shutil
import unittest

from nose.plugins.attrib import attr

from w3af.plugins.attack.db.sqlmap_wrapper import SQLMapWrapper, Target
from w3af.core.data.parsers.url import URL
from w3af.core.data.url.extended_urllib import ExtendedUrllib


@attr('moth')
class TestSQLMapWrapper(unittest.TestCase):
    
    SQLI_GET = 'http://moth/w3af/audit/sql_injection/select/'\
               'sql_injection_string.php?name=andres'

    SSL_SQLI_GET = 'http://moth/w3af/audit/sql_injection/select/'\
                   'sql_injection_string.php?name=andres'

    SQLI_POST = 'http://moth/w3af/audit/sql_injection/select/'\
                'sql_injection_string.php'
    
    DATA_POST = 'name=andres'
    
    def setUp(self):
        uri = URL(self.SQLI_GET)
        target = Target(uri)
        
        self.uri_opener = ExtendedUrllib()
        
        self.sqlmap = SQLMapWrapper(target, self.uri_opener)
    
    def tearDown(self):
        self.uri_opener.end()
        self.sqlmap.cleanup()
    
    @classmethod
    def setUpClass(cls):
        output_dir = os.path.join(SQLMapWrapper.SQLMAP_LOCATION, 'output')
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)

    @classmethod
    def tearDownClass(cls):
        # Doing this in both setupclass and teardownclass in order to be sure
        # that a ctrl+c doesn't break it
        output_dir = os.path.join(SQLMapWrapper.SQLMAP_LOCATION, 'output')
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        
    @attr('ci_fails')
    def test_verify_vulnerability(self):
        vulnerable = self.sqlmap.is_vulnerable()
        self.assertTrue(vulnerable)
    
    @attr('ci_fails')
    def test_verify_vulnerability_ssl(self):
        uri = URL(self.SSL_SQLI_GET)
        target = Target(uri)
        
        self.uri_opener = ExtendedUrllib()
        
        self.sqlmap = SQLMapWrapper(target, self.uri_opener)
        vulnerable = self.sqlmap.is_vulnerable()
        self.assertTrue(vulnerable)

    def test_verify_vulnerability_false(self):
        not_vuln = 'http://moth/w3af/audit/sql_injection/select/'\
                   'sql_injection_string.php?fake=invalid'
        uri = URL(not_vuln)
        target = Target(uri)
        
        self.sqlmap = SQLMapWrapper(target, self.uri_opener)
        
        vulnerable = self.sqlmap.is_vulnerable()
        self.assertFalse(vulnerable)
        
    @attr('ci_fails')
    def test_verify_vulnerability_POST(self):
        target = Target(URL(self.SQLI_POST), self.DATA_POST)
        
        self.sqlmap = SQLMapWrapper(target, self.uri_opener)
        
        vulnerable = self.sqlmap.is_vulnerable()
        self.assertTrue(vulnerable)
        
    def test_wrapper_invalid_url(self):
        self.assertRaises(TypeError, SQLMapWrapper, self.SQLI_GET, self.uri_opener)
    
    def test_stds(self):
        uri = URL(self.SQLI_GET)
        target = Target(uri)
        
        self.sqlmap = SQLMapWrapper(target, self.uri_opener)
        
        prms = ['--batch',]
        cmd, process = self.sqlmap.run_sqlmap_with_pipes(prms)
        
        self.assertIsInstance(process.stdout, file)
        self.assertIsInstance(process.stderr, file)
        self.assertIsInstance(process.stdin, file)
        self.assertIsInstance(cmd, basestring)
        
        self.assertIn('sqlmap.py', cmd)
        
    def test_target_basic(self):
        target = Target(URL(self.SQLI_GET))
        params = target.to_params()
        
        self.assertEqual(params, ["--url=%s" % self.SQLI_GET])
    
    def test_target_post_data(self):
        target = Target(URL(self.SQLI_GET), self.DATA_POST)
        params = target.to_params()
        
        self.assertEqual(params, ["--url=%s" % self.SQLI_GET,
                                  "--data=%s" % self.DATA_POST])
    
    def test_no_coloring(self):
        params = self.sqlmap.get_wrapper_params()
        self.assertIn('--disable-coloring', params)

    def test_always_batch(self):
        params = self.sqlmap.get_wrapper_params()
        self.assertIn('--batch', params)
        
    def test_use_proxy(self):
        params = self.sqlmap.get_wrapper_params()
        
        self.assertTrue(any(i.startswith('--proxy=http://127.0.0.1:') for i in params))

    def test_enable_coloring(self):
        uri = URL(self.SQLI_GET)
        target = Target(uri)
        
        sqlmap = SQLMapWrapper(target, self.uri_opener, coloring=True)
        params = sqlmap.get_wrapper_params()
        self.assertNotIn('--disable-coloring', params)
        
    @attr('ci_fails')
    def test_dbs(self):
        vulnerable = self.sqlmap.is_vulnerable()
        self.assertTrue(vulnerable)
        
        cmd, process = self.sqlmap.dbs()
        output = process.stdout.read()
        
        self.assertIn('fetching database names', output)
        self.assertIn('available databases', output)
        self.assertIn('information_schema', output)

    @attr('ci_fails')
    def test_tables(self):
        vulnerable = self.sqlmap.is_vulnerable()
        self.assertTrue(vulnerable)
        
        cmd, process = self.sqlmap.tables()
        output = process.stdout.read()
        
        self.assertIn('fetching tables for databases:', output)
        self.assertIn('Database: information_schema', output)
        self.assertIn('COLUMN_PRIVILEGES', output)

    @attr('ci_fails')
    def test_users(self):
        vulnerable = self.sqlmap.is_vulnerable()
        self.assertTrue(vulnerable)
        
        cmd, process = self.sqlmap.users()
        output = process.stdout.read()
        
        self.assertIn('debian-sys-maint', output)
        self.assertIn('localhost', output)
        self.assertIn('root', output)

    @attr('ci_fails')
    def test_dump(self):
        vulnerable = self.sqlmap.is_vulnerable()
        self.assertTrue(vulnerable)
        
        cmd, process = self.sqlmap.dump()
        output = process.stdout.read()
        
        self.assertIn('email', output)
        self.assertIn('phone', output)
        self.assertIn('address', output)
        self.assertIn('47789900', output)
        
    @attr('ci_fails')
    def test_sqlmap(self):
        vulnerable = self.sqlmap.is_vulnerable()
        self.assertTrue(vulnerable)
        
        cmd, process = self.sqlmap.direct('--dump -D w3af_test -T users')
        output = process.stdout.read()
        
        self.assertIn('email', output)
        self.assertIn('phone', output)
        self.assertIn('address', output)
        self.assertIn('47789900', output)
        
        self.assertNotIn('information_schema', output)
        self.assertNotIn('COLUMN_PRIVILEGES', output)