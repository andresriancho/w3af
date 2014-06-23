"""
test_crackme_cenzic_com.py

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


class TestScanCrackmeCenzicCom(TestScanVulnerableSite, PluginTest):

    target_url = 'http://crackme.cenzic.com'
    EXPECTED_VULNS = {('Interesting HTML comment', u'/Kelev/view/credit.php', None),
                      ('HTML comment contains HTML code', u'/Kelev/view/loanrequest.php', None),
                      ('Interesting HTML comment', u'/Kelev/loans/studentloan.php', None),
                      ('Interesting HTML comment', u'/Kelev/view/terms.php', None),
                      ('Interesting HTML comment', u'/Kelev/view/privacy.php', None),
                      ('Strange HTTP response code', u'/WGVbF', None),
                      ('Interesting HTML comment', u'/Kelev/view/kelev2.php', None),
                      ('Auto-completable form', u'/Kelev/php/loginbm.php', None),
                      ('Unidentified vulnerability', u'/Kelev/view/updateloanrequest.php', 'drpLoanType'),
                      ('Server header', None, None),
                      ('Interesting HTML comment', u'/Kelev/register/register.php', None),
                      ('Interesting HTML comment', u'/Kelev/view/trade.php', None),
                      ('Allowed HTTP methods', u'/', None),
                      ('Unidentified vulnerability', u'/Kelev/view/updateloanrequest.php', 'txtDOB'),
                      ('Interesting HTML comment', u'/Kelev/view/billsonline.php', None),
                      ('Unidentified vulnerability', u'/Kelev/view/updateloanrequest.php', 'txtAddress'),
                      ('Interesting HTML comment', u'/Kelev/loans/homeloan.php', None),
                      ('Interesting HTML comment', u'/Kelev/php/login.php', None),
                      ('Unidentified vulnerability', u'/Kelev/view/updateloanrequest.php', 'txtTelephoneNo'),
                      ('Unidentified vulnerability', u'/Kelev/view/updateloanrequest.php', 'txtCity'),
                      ('Cross site scripting vulnerability', u'/Kelev/view/updateloanrequest.php', 'txtFirstName'),
                      ('Powered-by header', None, None),
                      ('Unidentified vulnerability', u'/Kelev/view/updateloanrequest.php', 'drpState'),
                      ('Unidentified vulnerability', u'/Kelev/view/updateloanrequest.php', 'txtLastName'),
                      ('Interesting HTML comment', u'/Kelev/view/feedback.php', None),
                      ('SQL injection', u'/Kelev/view/updateloanrequest.php', 'txtAnnualIncome'),
                      ('Auto-completable form', u'/Kelev/php/login.php', None),
                      ('Interesting HTML comment', u'/Kelev/view/loanrequest.php', None),
                      ('Interesting HTML comment', u'/Kelev/loans/carloanmain.php', None),
                      ('Interesting HTML comment', u'/Kelev/view/netbanking.php', None),
                      ('Unidentified vulnerability', u'/Kelev/view/updateloanrequest.php', 'txtSocialScurityNo'),
                      ('Auto-completable form', u'/Kelev/register/register.php', None),
                      ('Strange HTTP Reason message', u'/Kelev/view/updateloanrequest.php', None),
                      ('Interesting HTML comment', u'/Kelev/php/loginbm.php', None),
                      ('Interesting HTML comment', u'/Kelev/view/rate.php', None),
                      ('Click-Jacking vulnerability', None, None),
                      ('Cross site tracing vulnerability', u'/', None),
                      ('Unidentified vulnerability', u'/Kelev/view/updateloanrequest.php', 'txtEmail'),
                      ('Interesting HTML comment', u'/Kelev/view/home.php', None)}
