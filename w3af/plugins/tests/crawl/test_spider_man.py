"""
test_spiderman.py

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
import time
import urllib2

from multiprocessing.dummy import Process

from w3af.core.controllers.misc.get_unused_port import get_unused_port
from w3af.core.controllers.ci.moth import get_moth_http, get_moth_https
from w3af.plugins.tests.helper import PluginTest, PluginConfig

BROWSE_URLS = (
    ('GET', '/audit/', None),
    ('GET', '/audit/sql_injection/where_integer_qs.py', 'id=1'),
    ('POST', '/audit/sql_injection/where_integer_form.py', 'text=abc'),
)

TERMINATE_URL = 'http://127.7.7.7/spider_man?terminate'


class BrowserThread(Process):

    def __init__(self, url_resolver, proxy_port):
        super(BrowserThread, self).__init__()
        self.responses = []
        self.url_resolver = url_resolver
        self.proxy_port = proxy_port

    def run(self):
        """
        @see: Comment in test_spiderman_basic
        """
        time.sleep(5.0)

        proxy_cfg = {'http': 'http://127.0.0.1:%s/' % self.proxy_port,
                     'https': 'http://127.0.0.1:%s/' % self.proxy_port}
        proxy_support = urllib2.ProxyHandler(proxy_cfg)
        opener = urllib2.build_opener(proxy_support)
        # Avoid this, it might influence other tests!
        #urllib2.install_opener(opener)

        all_urls = BROWSE_URLS

        for method, path, payload in all_urls:
            url = self.url_resolver(path)

            if method == 'POST':
                req = urllib2.Request(url, payload)
                response = opener.open(req)
            else:
                if payload is None:
                    full_url = url
                else:
                    full_url = url + '?' + payload
                response = opener.open(full_url)

            self.responses.append(response.read())

        response = opener.open(TERMINATE_URL)
        self.responses.append(response.read())


class TestSpiderman(PluginTest):

    def generic_spiderman_run(self, url_resolver=get_moth_http,
                              proxy_port=44444):
        """
        The difficult thing with this test is that the scan will block until
        we browse through the spider_man proxy to the spider_man.TERMINATE_URL,
        so we need to start a "browser thread" that will sleep for a couple
        of seconds before browsing through the proxy.

        The first assert will be performed between the links that we browse
        and the ones returned by the plugin to the core.

        The second assert will check that the proxy actually returned the
        expected HTTP response body to the browser.
        """
        bt = BrowserThread(url_resolver, proxy_port)
        bt.start()

        # pylint: disable=E1101
        cfg = self._run_configs['cfg']
        # pylint: enable=E1101
        self._scan(cfg['target'], cfg['plugins'])

        # Fetch all the results
        bt.join()
        kb_urls = self.kb.get_all_known_urls()
        responses = bt.responses

        EXPECTED_RESPONSE_CONTENTS = (
            'Trivial Blind SQL injection',
            'reachable using a query string',
            'no such column: abc',
            'spider_man plugin finished its execution.',
        )

        # The browser that used spiderman needs to get these responses
        for index, e_response in enumerate(EXPECTED_RESPONSE_CONTENTS):
            self.assertIn(e_response, responses[index])

        # w3af needs to know about the browsed URLs
        kb_urls = [u.uri2url().url_string for u in kb_urls]
        for _, e_url, _ in BROWSE_URLS:
            self.assertIn(url_resolver(e_url), kb_urls)


class TestHTTPSpiderman(TestSpiderman):

    base_url = get_moth_http()
    port = get_unused_port()

    _run_configs = {
        'cfg': {
            'target': base_url,
            'plugins': {'crawl': (PluginConfig('spider_man',

                                               ('listen_port', port, PluginConfig.INT),

                                               ),)}
        }
    }

    def test_spiderman_http(self):
        self.generic_spiderman_run(get_moth_http, self.port)


class TestHTTPSSpiderman(TestSpiderman):

    base_url = get_moth_https()
    port = get_unused_port()

    _run_configs = {
        'cfg': {
            'target': base_url,
            'plugins': {'crawl': (PluginConfig('spider_man',

                                               ('listen_port', port, PluginConfig.INT),

                                               ),)}
        }
    }

    def test_spiderman_https(self):
        self.generic_spiderman_run(get_moth_https, self.port)