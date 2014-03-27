"""
test_get_emails.py

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
from nose.plugins.attrib import attr

from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig


@attr('ci_ready')
class TestGetEmails(PluginTest):

    get_emails_url = get_moth_http('/grep/get_emails/')

    _run_configs = {
        'cfg1': {
            'target': get_emails_url,
            'plugins': {
                'grep': (PluginConfig('get_emails',
                                      (
                                          'only_target_domain', False, PluginConfig.BOOL)),),
                'crawl': (
                    PluginConfig('web_spider',
                                 ('only_forward', True, PluginConfig.BOOL)),
                )

            }
        }
    }

    def test_found_emails(self):
        cfg = self._run_configs['cfg1']
        self._scan(cfg['target'], cfg['plugins'])

        target_emails = self.kb.get('emails', 'emails')
        self.assertEqual(len(target_emails), 0)

        all_email_infos = self.kb.get('emails', 'external_emails')
        all_emails = set([i['mail'] for i in all_email_infos])

        EXPECTED = set([u'f00@moth.com', u'bar@moth.com', u'hello@world.com',
                        u'world@f00.net', u'planer@moth.com', u'pp@moth.com',
                        u'notme@gmail.com'])

        self.assertEqual(all_emails, EXPECTED)
