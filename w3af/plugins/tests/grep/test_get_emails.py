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
import unittest

import w3af.core.data.kb.knowledge_base as kb
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.headers import Headers
from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.plugins.grep.get_emails import get_emails
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.plugins.tests.helper import PluginTest, PluginConfig


class TestGetEmails(PluginTest):

    get_emails_url = get_moth_http('/grep/get_emails/')

    _run_configs = {
        'cfg1': {
            'target': get_emails_url,
            'plugins': {
                'grep': (PluginConfig('get_emails',
                                      ('only_target_domain',
                                       False,
                                       PluginConfig.BOOL)),),
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

        expected = {u'one@moth.com',
                    u'two@moth.com',
                    u'three@moth.com',
                    u'four@moth.com'}

        all_email_info_sets = self.kb.get('emails', 'external_emails')
        self.assertEqual(len(all_email_info_sets), len(expected))

        all_emails = set([i.get_attribute('mail') for i in all_email_info_sets])
        self.assertEqual(all_emails, expected)


class RawTestGetEmail(unittest.TestCase):
    def setUp(self):
        create_temp_dir()
        kb.kb.cleanup()
        self.plugin = get_emails()

    def tearDown(self):
        self.plugin.end()

    def test_group_by_email(self):
        headers = Headers([('content-type', 'text/html')])

        body_1 = '<a href="mailto:one@w3af.com">test one</a>'
        url_1 = URL('http://www.w3af.com/1')
        request_1 = FuzzableRequest(url_1, method='GET')
        resp_1 = HTTPResponse(200, body_1, headers, url_1, url_1, _id=1)
        self.plugin.grep(request_1, resp_1)

        body_2 = '<a href="mailto:one@w3af.com">test two</a>'
        url_2 = URL('http://www.w3af.com/2')
        request_2 = FuzzableRequest(url_2, method='GET')
        resp_2 = HTTPResponse(200, body_2, headers, url_2, url_2, _id=2)
        self.plugin.grep(request_2, resp_2)

        info_sets = kb.kb.get('emails', 'emails')
        self.assertEquals(len(info_sets), 1)

        expected_desc = u'The application discloses the "one@w3af.com" email' \
                        u' address in 2 different HTTP responses. The first' \
                        u' ten URLs which sent the email are:\n' \
                        u' - http://www.w3af.com/2\n - http://www.w3af.com/1\n'

        info_set = info_sets[0]
        self.assertEqual(info_set.get_id(), [1, 2])
        self.assertEqual(info_set.get_desc(), expected_desc)
