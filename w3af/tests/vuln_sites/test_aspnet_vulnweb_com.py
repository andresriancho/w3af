"""
test_aspnet_vulnweb_com.py

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


class TestScanASPNETVulnwebCom(TestScanVulnerableSite, PluginTest):

    target_url = 'http://testaspnet.vulnweb.com/'
    EXPECTED_VULNS = {('.NET ViewState encryption is disabled', u'/', None),
                      ('Uncommon query string parameter', u'/ReadNews.aspx', None),
                      ('Interesting META tag', u'/Default.aspx', None),
                      ('Uncommon query string parameter', u'/Comments.aspx', None),
                      ('.NET ViewState encryption is disabled', u'/about.aspx', None),
                      ('Interesting META tag', u'/', None),
                      ('Blind SQL injection vulnerability', u'/login.aspx', 'tbUsername'),
                      ('Interesting META tag', u'/ReadNews.aspx', None),
                      ('CSRF vulnerability', u'/ReadNews.aspx', None),
                      ('Blind SQL injection vulnerability', u'/ReadNews.aspx', u'id'),
                      ('CSRF vulnerability', u'/Comments.aspx', None),
                      ('Auto-completable form', u'/Signup.aspx', None),
                      ('Server header', None, None),
                      ('Phishing vector', u'/ReadNews.aspx', u'NewsAd'),
                      ('Auto-completable form', u'/login.aspx', None),
                      ('Interesting META tag', u'/Comments.aspx', None),
                      ('ReDoS vulnerability', u'/ReadNews.aspx', u'id'),
                      ('.NET ViewState encryption is disabled', u'/default.aspx', None),
                      ('.NET ViewState encryption is disabled', u'/login.aspx', None),
                      ('Cross site scripting vulnerability', u'/ReadNews.aspx', u'NewsAd'),
                      ('Powered-by header', None, None),
                      ('.NET ViewState encryption is disabled', u'/Comments.aspx', None),
                      ('Interesting META tag', u'/Signup.aspx', None),
                      ('Content feed resource', u'/rssFeed.aspx', None),
                      ('Blind SQL injection vulnerability', u'/Comments.aspx', 'tbComment'),
                      ('.NET ViewState encryption is disabled', u'/Default.aspx', None),
                      ('Blank http response body', u'/ReadNews.aspx', None),
                      ('Unhandled error in web application', u'/ReadNews.aspx', None),
                      ('Cross site scripting vulnerability', u'/Comments.aspx', 'tbComment'),
                      ('Interesting META tag', u'/about.aspx', None),
                      ('Blind SQL injection vulnerability', u'/Comments.aspx', u'id'),
                      ('Interesting META tag', u'/default.aspx', None),
                      ('OS commanding vulnerability', u'/ReadNews.aspx', u'id'),
                      ('.NET ViewState encryption is disabled', u'/ReadNews.aspx', None),
                      ('Click-Jacking vulnerability', None, None),
                      ('Allowed HTTP methods', u'/', None),
                      ('Interesting META tag', u'/login.aspx', None),
                      ('Blank http response body', u'/Comments.aspx', None),
                      ('.NET ViewState encryption is disabled', u'/Signup.aspx', None)}
