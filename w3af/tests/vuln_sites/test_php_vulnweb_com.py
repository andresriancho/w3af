"""
test_php_vulnweb_com.py

Copyright 2014 Andres Riancho

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
from w3af.tests.vuln_sites.utils.scan_vulnerable_site import TestScanVulnerableSite
from w3af.plugins.tests.helper import PluginTest


class TestScanPHPVulnwebCom(TestScanVulnerableSite, PluginTest):

    target_url = 'http://testphp.vulnweb.com/'
    EXPECTED_VULNS = {('Uncommon query string parameter', u'/showimage.php', None),
                      ('SQL injection', u'/listproducts.php', u'cat'),
                      ('Browser plugin content', u'/signup.php', None),
                      ('Strange HTTP response code', u'/kjxcn', None),
                      ('Browser plugin content', u'/cart.php', None),
                      ('AJAX code', u'/AJAX/index.php', None),
                      ('Cross site scripting vulnerability', u'/guestbook.php', 'name'),
                      ('Uncommon query string parameter', u'/hpp/params.php', None),
                      ('Path disclosure vulnerability', u'/artists.php', None),
                      ('Browser plugin content', u'/artists.php', None),
                      ('Directory indexing', u'/Flash/', None),
                      ('Browser plugin content', u'/index.php', None),
                      ('SQL injection', u'/product.php', u'pic'),
                      ('Browser plugin content', u'/login.php', None),
                      ('Path disclosure vulnerability', u'/search.php', None),
                      ('SQL injection', u'/userinfo.php', 'pass'),
                      ('Cross site scripting vulnerability', u'/secured/newuser.php', 'uemail'),
                      ('SQL injection', u'/search.php', u'test'),
                      ('Path disclosure vulnerability', u'/guestbook.php', None),
                      ('Browser plugin content', u'/listproducts.php', None),
                      ('Server header', None, None),
                      ('Path disclosure vulnerability', u'/listproducts.php', None),
                      ('Powered-by header', None, None),
                      ('Auto-completable form', u'/signup.php', None),
                      ('SQL injection', u'/secured/newuser.php', 'uuname'),
                      ('Browser plugin content', u'/', None),
                      ('Cross site scripting vulnerability', u'/guestbook.php', 'text'),
                      ('Cross site scripting vulnerability', u'/secured/newuser.php', 'uphone'),
                      ('Insecure redirection', u'/redir.php', u'r'),
                      ('Path disclosure vulnerability', u'/hpp/params.php', None),
                      ('Browser plugin content', u'/disclaimer.php', None),
                      ('Unhandled error in web application', u'/redir.php', None),
                      ('Auto-completable form', u'/login.php', None),
                      ('Cross site scripting vulnerability', u'/secured/newuser.php', 'uuname'),
                      ('Cross site scripting vulnerability', u'/showimage.php', u'file'),
                      ('Allowed HTTP methods', u'/', None),
                      ('Blank http response body', u'/secured/', None),
                      ('Cross site scripting vulnerability', u'/search.php', 'searchFor'),
                      ('Parameter modifies response headers', u'/redir.php', u'r'),
                      ('SQL injection', u'/userinfo.php', 'uname'),
                      ('SQL injection', u'/listproducts.php', u'artist'),
                      ('Cross site scripting vulnerability', u'/hpp/params.php', u'p'),
                      ('Strange HTTP response code', u'/redir.php', None),
                      ('Path disclosure vulnerability', u'/redir.php', None),
                      ('Browser plugin content', u'/search.php', None),
                      ('Cross site scripting vulnerability', u'/hpp/params.php', u'pp'),
                      ('Remote file inclusion', u'/showimage.php', u'file'),
                      ('Browser plugin content', u'/guestbook.php', None),
                      ('Cross site scripting vulnerability', u'/hpp/', u'pp'),
                      ('Cross site scripting vulnerability', u'/secured/newuser.php', 'uaddress'),
                      ('Cross site scripting vulnerability', u'/secured/newuser.php', 'urname'),
                      ('Click-Jacking vulnerability', None, None),
                      ('AJAX code', u'/AJAX/', None),
                      ('Browser plugin content', u'/categories.php', None),
                      ('Browser plugin content', u'/product.php', None),
                      ('SQL injection', u'/artists.php', u'artist'),
                      ('Path disclosure vulnerability', u'/product.php', None),
                      ('Potential buffer overflow vulnerability', u'/showimage.php', u'size'),
                      ('Strange HTTP Reason message', u'/redir.php', None),
                      ('Cross site scripting vulnerability', u'/secured/newuser.php', 'ucc'),
                      ('Local file inclusion vulnerability', u'/showimage.php', u'file')}
