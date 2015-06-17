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
import socket
import urllib2

from multiprocessing.dummy import Process

from w3af.core.controllers.misc.get_unused_port import get_unused_port
from w3af.core.controllers.ci.moth import get_moth_http, get_moth_https
from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.plugins.crawl.spider_man import TERMINATE_URL

BROWSE_URLS = (
    ('GET', '/audit/', None),
    ('GET', '/audit/sql_injection/where_integer_qs.py', 'id=1'),
    ('POST', '/audit/sql_injection/where_integer_form.py', 'text=abc'),
)


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

        # Wait for the proxy to start
        for i in xrange(120):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect(('127.0.0.1', self.proxy_port))
            except:
                time.sleep(0.5)
            else:
                break

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
                try:
                    response = opener.open(req)
                except Exception, ex:
                    self.responses.append(str(ex))
                else:
                    self.responses.append(response.read())
            else:
                if payload is None:
                    full_url = url
                else:
                    full_url = url + '?' + payload

                try:
                    response = opener.open(full_url)
                except Exception, ex:
                    self.responses.append(str(ex))
                else:
                    self.responses.append(response.read())

        try:
            response = opener.open(TERMINATE_URL.url_string)
        except Exception, ex:
            self.responses.append(str(ex))
        else:
            self.responses.append(response.read())


class TestSpiderman(PluginTest):

    def generic_spiderman_run(self,
                              run_config,
                              url_resolver=get_moth_http,
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

        self._scan(run_config['target'], run_config['plugins'])

        # Fetch all the results
        bt.join()
        kb_urls = self.kb.get_all_known_urls()
        responses = bt.responses

        expected_response_contents = (
            'Trivial Blind SQL injection',
            'reachable using a query string',
            'no such column: abc',
            'spider_man plugin finished its execution.',
        )

        # The browser that used spiderman needs to get these responses
        for index, e_response in enumerate(expected_response_contents):
            self.assertIn(e_response, responses[index])

        # w3af needs to know about the browsed URLs
        kb_urls = [u.uri2url().url_string for u in kb_urls]
        for _, e_url, _ in BROWSE_URLS:
            self.assertIn(url_resolver(e_url), kb_urls)


class TestHTTPSpiderman(TestSpiderman):

    def test_spiderman_http(self):
        port = get_unused_port()

        run_config = {
                'target': get_moth_http(),
                'plugins': {'crawl': (PluginConfig('spider_man',
                                                   ('listen_port', port,
                                                    PluginConfig.INT),
                                                   ),)}
        }

        self.generic_spiderman_run(run_config, get_moth_http, port)


class TestHTTPSSpiderman(TestSpiderman):

    def test_spiderman_https(self):
        port = get_unused_port()

        run_config = {
                'target': get_moth_https(),
                'plugins': {'crawl': (PluginConfig('spider_man',
                                                   ('listen_port', port,
                                                    PluginConfig.INT),
                                                   ),)}
        }

        self.generic_spiderman_run(run_config, get_moth_https, port)