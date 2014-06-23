"""
test_demo_testfire_net.py

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
from w3af.plugins.tests.helper import PluginTest
from w3af.tests.vuln_sites.utils.scan_vulnerable_site import TestScanVulnerableSite


class TestDemoTestFireNet(TestScanVulnerableSite, PluginTest):
    target_url = 'http://demo.testfire.net/'
    EXPECTED_VULNS = {('CSRF vulnerability', u'/search.aspx', None),
                      ('SQL injection', u'/bank/login.aspx', 'uid'),
                      ('Cross site scripting vulnerability', u'/comment.aspx', 'name'),
                      ('Cookie without HttpOnly', u'/bank/apply.aspx', None),
                      ('Cookie without HttpOnly', u'/bank/account.aspx', None),
                      ('Uncommon query string parameter', u'/legal/us/en/', None),
                      ('Server header', None, None),
                      ('CSRF vulnerability', u'/default.aspx', None),
                      ('Cross site scripting vulnerability', u'/search.aspx', 'txtSearch'),
                      ('Cookie without HttpOnly', u'/bank/logout.aspx', None),
                      ('CSRF vulnerability', u'/servererror.aspx', None),
                      ('CSRF vulnerability', u'/survey_questions.aspx', None),
                      ('Cookie without HttpOnly', u'/bank/main.aspx', None),
                      ('Cookie without HttpOnly', u'/bank/customize.aspx', None),
                      ('Interesting HTML comment', u'/feedback.aspx', None),
                      ('Powered-by header', None, None),
                      ('CSRF vulnerability', u'/bank/ws.asmx', None),
                      ('HTTP Basic authentication', u'/bank/members/_vti_bin/_vti_aut/author.dll', None),
                      ('Unhandled error in web application', u'/bank/ws.asmx', None),
                      ('HTTP Response in HTTP body', u'/bank/ws.asmx', None),
                      ('Auto-completable form', u'/bank/login.aspx', None),
                      ('Cookie without HttpOnly', u'/bank/transaction.aspx', None),
                      ('HTTP Basic authentication', u'/bank/members/', None),
                      ('SQL injection', u'/bank/login.aspx', 'passw'),
                      ('Click-Jacking vulnerability', None, None),
                      ('Cookie', u'/bank/customize.aspx', None),
                      ('Cookie without HttpOnly', u'/bank/transfer.aspx', None),
                      ('Allowed HTTP methods', u'/', None),
                      ('Cross site scripting vulnerability', u'/bank/login.aspx', 'uid'),
                      ('Cookie', u'/bank/transfer.aspx', None),
                      ('Cross-domain javascript source', u'/def,ault.aspx', None),
                      ('HTTP Request in HTTP body', u'/bank/ws.asmx', None),
                      ('Cookie', u'/bank/apply.aspx', None)}
