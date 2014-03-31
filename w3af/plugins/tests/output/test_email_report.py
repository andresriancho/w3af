"""
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
"""
from mock import patch
from nose.plugins.attrib import attr

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig


@attr('moth')
class TestEmailReport(PluginTest):

    target_url = get_moth_http('/audit/xss/')
    to_addrs = 'w3af@mailinator.com'
    from_addr = 'w3af@gmail.com'

    _run_configs = {
        'cfg': {
            'target': target_url,
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
                        ('toAddrs', to_addrs, PluginConfig.LIST),
                        ('fromAddr', from_addr, PluginConfig.STR),
                    ),
                )
            },
        }
    }

    def test_found_xss(self):
        # monkey-patch smtplib so we don't send actual emails
        inbox = []

        class Message(object):
            def __init__(self, from_address, to_address, fullmessage):
                self.from_address = from_address
                self.to_address = to_address
                self.fullmessage = fullmessage

        class DummySMTP(object):
            def __init__(self):
                smtp = self

            def login(self, username, password):
                self.username = username
                self.password = password

            def sendmail(self, from_address, to_address, fullmessage):
                inbox.append(Message(from_address, to_address, fullmessage))
                return []

            def quit(self):
                self.has_quit = True

        cfg = self._run_configs['cfg']

        with patch('w3af.plugins.output.email_report.smtplib.SMTP') as mock_smtp:
            mock_smtp.return_value = DummySMTP()

            self._scan(cfg['target'], cfg['plugins'])

            xss_vulns = self.kb.get('xss', 'xss')

            self.assertEqual(len(inbox), 1)
            email_msg = inbox[0]

            self.assertEqual(email_msg.from_address, self.from_addr)
            self.assertEqual(email_msg.to_address, [self.to_addrs,])

            content = email_msg.fullmessage
            xss_count = 0
            pxss_count = 0
            
            for line in content.split('\n'):
                if 'A Cross Site Scripting vulnerability was found at:' in line:
                    xss_count += 1
                elif 'A persistent Cross Site Scripting vulnerability' in line:
                    pxss_count += 1
            
            self.assertEqual(len(xss_vulns), xss_count + pxss_count)


