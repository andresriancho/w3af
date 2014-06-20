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
from nose.plugins.attrib import attr

from w3af.plugins.tests.helper import PluginTest, PluginConfig


EXPECTED_URLS = {
    u'/bank/ws.asmx?op=GetUserAccounts',
    u'/bank/transfer.aspx',
    u'/survey_questions.aspx?step=a',
    u'/default.aspx?content=inside_about.htm',
    u'/bank/bank.master.cs',
    u'/bank/apply.aspx',
    u'/servererror.aspx?aspxerrorpath=%2Fbank%2Fbank.master',
    u'/images/DownloadAppScanDemo_172x80.jpg',
    u'/bank/account.aspx',
    u'/bank/ws.asmx',
    u'/bank/20060308_bak/',
    u'/bank/',
    u'/style.css',
    u'/bank/main.aspx',
    u'/images/p_checking.jpg',
    u'/search.aspx',
    u'/servererror.aspx?aspxerrorpath=%2Fbank%2Faccount.aspx.cs',
    u'/default.aspx?content=inside_careers.htm',
    u'/bank/members/',
    u'/images/home2.jpg',
    u'/images/inside5.jpg',
    u'/bank/login.aspx.cs',
    u'/images/inside7.jpg',
    u'/comment.aspx',
    u'/',
    u'/bank/transaction.aspx.cs',
    u'/bank/bank.master',
    u'/images/home1.jpg',
    u'/bank/customize.aspx.cs',
    u'/images/pf_lock.gif',
    u'/default.aspx?content=personal_checking.htm',
    u'/bank/mozxpath.js',
    u'/bank/logout.aspx',
    u'/bank/ws.asmx?op=TransferBalance',
    u'/bank/customize.aspx',
    u'/default.aspx?content=inside_press.htm',
    u'/bank/servererror.aspx',
    u'/Privacypolicy.aspx?sec=Careers&template=US',
    u'/bank/ws.asmx?op=IsValidUser',
    u'/bank/logout.aspx.cs',
    u'/search.aspx?txtSearch=',
    u'/images/inside4.jpg',
    u'/feedback.aspx',
    u'/images/inside3.jpg',
    u'/bank/apply.aspx.cs',
    u'/images/home3.jpg',
    u'/bank/queryxpath.aspx.cs',
    u'/bank/queryxpath.aspx',
    u'/bank/main.aspx.cs',
    u'/default.aspx',
    u'/bank/login.aspx',
    u'/bank/transaction.aspx',
    u'/bank/account.aspx.cs',
    u'/bank/ws.asmx?disco=',
    u'/bank/ws.asmx?WSDL=',
    u'/survey_questions.aspx',
    u'/servererror.aspx?aspxerrorpath=%2Fbank%2Fcustomize.aspx.cs',
    u'/images/logo.gif',
    u'/default.aspx?content=inside_investor.htm',
    u'/bank/transfer.aspx.cs',
    u'/images/header_pic.jpg'}

EXPECTED_VULNS = {()}


@attr('functional')
@attr('internet')
@attr('slow')
@attr('ci_fails')
class TestDemoTestFireNet(PluginTest):

    target_url = 'http://demo.testfire.net/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {
                'crawl': (PluginConfig('web_spider',),),
                'audit': (PluginConfig('all'),),
                'grep': (PluginConfig('all'),),
            }
        }
    }

    def test_scan_demo_testfire_net(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        self.assertAllURLsFound(EXPECTED_URLS)
        self.assertAllExpectedVulnsFound(EXPECTED_VULNS)