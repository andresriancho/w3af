"""
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
"""
import os
import shutil
import unittest

from nose.plugins.attrib import attr

from w3af.core.controllers.ci.moth import get_moth_http, get_moth_https
from w3af.plugins.attack.db.sqlmap_wrapper import SQLMapWrapper, Target
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.url.extended_urllib import ExtendedUrllib


@attr('moth')
class TestSQLMapWrapper(unittest.TestCase):
    
    SQLI_GET = get_moth_http('/audit/sql_injection/'
                             'where_string_single_qs.py?uname=pablo')

    SSL_SQLI_GET = get_moth_https('/audit/sql_injection/'
                                  'where_string_single_qs.py?uname=pablo')

    SQLI_POST = get_moth_http('/audit/sql_injection/where_integer_form.py')
    
    DATA_POST = 'text=1'
    
    def setUp(self):
        uri = URL(self.SQLI_GET)
        target = Target(uri)
        
        self.uri_opener = ExtendedUrllib()
        
        self.sqlmap = SQLMapWrapper(target, self.uri_opener, debug=True)
    
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
        
    def test_verify_vulnerability(self):
        vulnerable = self.sqlmap.is_vulnerable()
        self.assertTrue(vulnerable)
    
    def test_verify_vulnerability_ssl(self):
        uri = URL(self.SSL_SQLI_GET)
        target = Target(uri)
        
        self.uri_opener = ExtendedUrllib()
        
        self.sqlmap = SQLMapWrapper(target, self.uri_opener)
        vulnerable = self.sqlmap.is_vulnerable()
        self.assertTrue(vulnerable, self.sqlmap.last_stdout)

    def test_verify_vulnerability_false(self):
        not_vuln = get_moth_http('/audit/sql_injection/'
                                 'where_string_single_qs.py?fake=pablo')
        uri = URL(not_vuln)
        target = Target(uri)
        
        self.sqlmap = SQLMapWrapper(target, self.uri_opener)
        
        vulnerable = self.sqlmap.is_vulnerable()
        self.assertFalse(vulnerable)
        
    def test_verify_vulnerability_POST(self):
        target = Target(URL(self.SQLI_POST), self.DATA_POST)
        
        self.sqlmap = SQLMapWrapper(target, self.uri_opener)
        
        vulnerable = self.sqlmap.is_vulnerable()
        self.assertTrue(vulnerable, self.sqlmap.last_stdout)
        
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
        
    def test_dbs(self):
        vulnerable = self.sqlmap.is_vulnerable()
        self.assertTrue(vulnerable)
        
        cmd, process = self.sqlmap.dbs()
        output = process.stdout.read()
        
        self.assertIn('on SQLite it is not possible to enumerate databases', output)

    def test_tables(self):
        vulnerable = self.sqlmap.is_vulnerable()
        self.assertTrue(vulnerable)
        
        cmd, process = self.sqlmap.tables()
        output = process.stdout.read()
        
        self.assertIn('auth_group_permissions', output)
        self.assertIn('Database: SQLite_masterdb', output)
        self.assertIn('django_content_type', output)

    def test_users(self):
        vulnerable = self.sqlmap.is_vulnerable()
        self.assertTrue(vulnerable)
        
        cmd, process = self.sqlmap.users()
        output = process.stdout.read()
        
        self.assertIn('on SQLite it is not possible to enumerate the users',
                      output)

    def test_dump(self):
        vulnerable = self.sqlmap.is_vulnerable()
        self.assertTrue(vulnerable)
        
        cmd, process = self.sqlmap.dump()
        output = process.stdout.read()
        
        self.assertIn('django_session', output)
        self.assertIn('auth_user_user_permissions', output)
        
    def test_sqlmap(self):
        vulnerable = self.sqlmap.is_vulnerable()
        self.assertTrue(vulnerable, self.sqlmap.last_stdout)
        
        cmd, process = self.sqlmap.direct('--tables')
        output = process.stdout.read()
        
        self.assertIn('django_session', output)
        self.assertIn('auth_user_user_permissions', output)
        
        self.assertNotIn('COLUMN_PRIVILEGES', output)