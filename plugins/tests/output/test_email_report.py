'''
test_email_report.py

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
import poplib

from plugins.tests.helper import PluginTest, PluginConfig


class TestEmailReport(PluginTest):

    xss_url = 'http://moth/w3af/audit/xss/'

    _run_configs = {
        'cfg': {
            'target': xss_url,
            'plugins': {
                'audit': (
                    PluginConfig(
                        'xss',
                         ('checkStored', True, PluginConfig.BOOL),
                         ('numberOfChecks', 3, PluginConfig.INT)),
                ),
                'crawl': (
                    PluginConfig(
                        'web_spider',
                        ('only_forward', True, PluginConfig.BOOL)),
                ),
                'output': (
                    PluginConfig(
                        'email_report',
                        ('smtpServer',
                         'smtp.mailinator.com', PluginConfig.STR),
                        ('smtpPort', 25, PluginConfig.INT),
                        ('toAddrs', 'w3af@mailinator.com', PluginConfig.LIST),
                        ('fromAddr', 'w3af@gmail.com', PluginConfig.STR),
                    ),
                )
            },
        }
    }

    def test_found_xss(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        xss_vulns = self.kb.get('xss', 'xss')
        xss_count = self._from_pop3_get_vulns()

        self.assertGreaterEqual(len(xss_vulns), 10)
        self.assertEqual(len(xss_vulns), xss_count)

    def _from_pop3_get_vulns(self):
        subject = None
        xss_count = 0

        pop_conn = poplib.POP3('pop.mailinator.com')
        pop_conn.user('w3af')
        pop_conn.pass_('somerand')

        num_messages = len(pop_conn.list()[1])
        for email_id in range(num_messages):
            for email_line in pop_conn.retr(email_id + 1)[1]:
                if email_line.startswith('Subject: '):
                    subject = email_line
                elif 'A Cross Site Scripting vulnerability was found at:' in email_line:
                    xss_count += 1
                elif 'A persistent Cross Site Scripting vulnerability' in email_line:
                    xss_count += 1

            pop_conn.dele(email_id + 1)

        pop_conn.quit()

        self.assertEqual(subject, 'Subject: [MAILINATOR] w3af report on http://moth/w3af/audit/xss/')

        return xss_count
