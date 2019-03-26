"""
test_payment_webhook_finder.py

Copyright 2019 Andres Riancho

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
from w3af.core.data.parsers.doc.url import URL
from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse
from w3af.plugins.crawl.payment_webhook_finder import payment_webhook_finder


def fill_kb_with_cgi_urls(target_url, add_url):
    """
    See payment_webhook_finder._get_extensions_for_fuzzing() to understand why
    we want to fill the KB with a lot of URLs with the same extension

    TL;DR speed-up test runs

    :param target_url: The target URL
    :param add_url: The method to use to write to the KB
    :return: None
    """
    for i in xrange(payment_webhook_finder.MIN_URL_COUNT_FOR_EXTENSION_FILTER + 1):
        url_str = '%s%s.cgi' % (target_url, i)
        url = URL(url_str)
        add_url(url)


class TestPaymentWebHookFinderGET(PluginTest):
    target_url = 'http://httpretty/'

    MOCK_RESPONSES = [MockResponse('http://httpretty/',
                                   body='index home page',
                                   method='GET',
                                   status=200),
                      MockResponse('http://httpretty/cgi-bin/paymentsuccessful.cgi',
                                   body='hidden',
                                   method='GET',
                                   status=200),
                      MockResponse('http://httpretty/.*',
                                   body='Not found',
                                   method='POST',
                                   status=404),
                      ]

    _run_config = {
        'target': target_url,
        'plugins': {'crawl': (PluginConfig('payment_webhook_finder'),)}
    }

    def test_find_using_GET(self):
        fill_kb_with_cgi_urls(self.target_url, self.kb.add_url)

        self._scan(self._run_config['target'], self._run_config['plugins'])

        urls = self.kb.get_all_known_urls()
        urls = [url.url_string for url in urls]

        self.assertIn(self.target_url + 'cgi-bin/paymentsuccessful.cgi', urls)


class TestPaymentWebHookFinderPOST(PluginTest):
    target_url = 'http://httpretty/'

    MOCK_RESPONSES = [MockResponse('http://httpretty/',
                                   body='index home page',
                                   method='GET',
                                   status=200),
                      MockResponse('http://httpretty/cgi-bin/paymentsuccessful.cgi',
                                   body='hidden',
                                   method='POST',
                                   status=200),
                      MockResponse('http://httpretty/.*',
                                   body='Not found',
                                   method='POST',
                                   status=404),
                      ]

    _run_config = {
        'target': target_url,
        'plugins': {'crawl': (PluginConfig('payment_webhook_finder'),)}
    }

    def test_find_using_POST(self):
        fill_kb_with_cgi_urls(self.target_url, self.kb.add_url)

        self._scan(self._run_config['target'], self._run_config['plugins'])

        urls = self.kb.get_all_known_urls()
        urls = [url.url_string for url in urls]

        self.assertIn(self.target_url + 'cgi-bin/paymentsuccessful.cgi', urls)

