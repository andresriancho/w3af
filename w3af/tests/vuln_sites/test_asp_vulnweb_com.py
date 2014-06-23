"""
test_asp_vulnweb_com.py

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


class TestScanASPVulnwebCom(TestScanVulnerableSite, PluginTest):

    target_url = 'http://testasp.vulnweb.com/'
    EXPECTED_VULNS = {('CSRF vulnerability', u'/showthread.asp', None),
                      ('SQL injection', u'/Register.asp', 'tfUName'),
                      ('Path disclosure vulnerability', u'/Search.asp', None),
                      ('Click-Jacking vulnerability', None, None),
                      ('CSRF vulnerability', u'/Search.asp', None),
                      ('Local file inclusion vulnerability', u'/Templatize.asp', u'item'),
                      ('Unhandled error in web application', u'/Search.asp', None),
                      ('SQL injection', u'/Login.asp', 'tfUName'),
                      ('Strange HTTP Reason message', u'/showforum.asp', None),
                      ('Unhandled error in web application', u'/Templatize.asp', None),
                      ('SQL injection', u'/Register.asp', 'tfRName'),
                      ('SQL injection', u'/showforum.asp', u'id'),
                      ('CSRF vulnerability', u'/Login.asp', None),
                      ('Server header', None, None),
                      ('SQL injection', u'/Register.asp', 'tfUPass'),
                      ('Cross site scripting vulnerability', u'/Search.asp', 'tfSearch'),
                      ('CSRF vulnerability', u'/Register.asp', None),
                      ('SQL injection', u'/showthread.asp', u'id'),
                      ('Cross site scripting vulnerability', u'/Login.asp', u'RetURL'),
                      ('Unhandled error in web application', u'/showthread.asp', None),
                      ('Unhandled error in web application', u'/Register.asp', None),
                      ('Powered-by header', None, None),
                      ('Insecure redirection', u'/Login.asp', u'RetURL'),
                      ('SQL injection', u'/Register.asp', 'tfEmail'),
                      ('Unhandled error in web application', u'/showforum.asp', None),
                      ('Descriptive error page', u'/Templatize.asp', None),
                      ('Auto-completable form', u'/Register.asp', None),
                      ('Uncommon query string parameter', u'/Logout.asp', None),
                      ('CSRF vulnerability', u'/Templatize.asp', None),
                      ('CSRF vulnerability', u'/showforum.asp', None),
                      ('SQL injection', u'/Login.asp', 'tfUPass'),
                      ('Unidentified vulnerability', u'/Register.asp', u'RetURL'),
                      ('SQL injection', u'/Search.asp', 'tfSearch'),
                      ('Auto-completable form', u'/Login.asp', None),
                      ('Allowed HTTP methods', u'/', None)}
