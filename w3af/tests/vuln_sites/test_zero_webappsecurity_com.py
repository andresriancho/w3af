"""
test_zero_webappsecurity_com.py

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


class TestZeroWebAppSecurityCom(TestScanVulnerableSite, PluginTest):

    target_url = 'http://zero.webappsecurity.com'
    EXPECTED_VULNS = {('CSRF vulnerability', u'/faq.html', None),
                      ('Interesting META tag', u'/faq.html', None),
                      ('DAV incorrect configuration', u'/gJEVl', None),
                      ('Interesting META tag', u'/', None),
                      ('Interesting META tag', u'/index.html', None),
                      ('Identified cookie', u'/bank/account-summary.html', None),
                      ('Interesting META tag', u'/help.html', None),
                      ('DAV methods enabled', u'/', None),
                      ('Cookie', u'/bank/account-summary.html', None),
                      ('Server header', None, None),
                      ('DAV incorrect configuration', u'/resources/css/ndAXD', None),
                      ('AJAX code', u'/resources/js/jquery-1.6.4.min.js', None),
                      ('Strange HTTP response code', u'/search.html', None),
                      ('DAV incorrect configuration', u'/resources/img/pkuJO', None),
                      ('Interesting META tag', u'/feedback.html', None),
                      ('DAV incorrect configuration', u'/resources/js/soyxK', None),
                      ('Identified cookie', u'/bank/transfer-funds.html', None),
                      ('Interesting META tag', u'/search.html', None),
                      ('CSRF vulnerability', u'/login.html', None),
                      ('Interesting META tag', u'/forgot-password.html', None),
                      ('Interesting META tag', u'/login.html', None),
                      ('Interesting META tag', u'/online-banking.html', None),
                      ('Click-Jacking vulnerability', None, None),
                      ('Strange HTTP response code', u'/sendFeedback.html', None)}
