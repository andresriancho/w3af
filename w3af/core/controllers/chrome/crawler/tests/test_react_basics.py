"""
test_react_basics.py

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
from w3af.core.controllers.chrome.crawler.tests.base import BaseChromeCrawlerTest


class ReactBasicTest(BaseChromeCrawlerTest):
    def test_react_hello_world_app(self):
        url = 'http://react-hello-world-app.surge.sh/'
        found_uris = self._crawl(url)

        expected_uris = {
            'http://react-hello-world-app.surge.sh/',
            'http://react-hello-world-app.surge.sh/static/css/main.4b51051d.css',
            'http://react-hello-world-app.surge.sh/static/js/main.d78accb8.js',
        }

        self.assertEqual(found_uris, expected_uris)

        expected_messages = '''
        Dispatching "click" on CSS selector "!document"
        Dispatching "click" on CSS selector ".AddGreeter button"
        The JS crawler noticed a big change in the DOM.
        Dispatching "click" on CSS selector ".HelloWorldList .HelloWorld:nth-of-type(2) button:nth-child(2)"
        Dispatching "click" on CSS selector ".HelloWorldList .HelloWorld:nth-of-type(2) button:nth-child(2) [role]"
        Dispatching "click" on CSS selector ".HelloWorldList .HelloWorld:nth-of-type(2) button:nth-child(3)"
        Dispatching "click" on CSS selector ".HelloWorldList .HelloWorld:nth-of-type(2) button:nth-child(3) [role]"
        Dispatching "click" on CSS selector ".HelloWorldList .HelloWorld:nth-of-type(2) button:nth-child(5)"
        The JS crawler noticed a big change in the DOM.
        Processing event 10 out of (unknown)
        '''

        found, not_found = self._log_contains(expected_messages)
        self.assertEqual(not_found, [])

    def test_react_autosuggest(self):
        url = 'https://dist-usikpayhrn.now.sh/'
        found_uris = self._crawl(url)

        expected_uris = {
            'https://api.github.com/repos/moroshko/react-autosuggest',
            'https://dist-usikpayhrn.now.sh/',
            'https://dist-usikpayhrn.now.sh/app.css',
            'https://dist-usikpayhrn.now.sh/autosuggest.css',
            'https://dist-usikpayhrn.now.sh/index.js',
            'https://fonts.googleapis.com/css?family=Open%20Sans:300|Open%20Sans:400',
            'https://fonts.gstatic.com/s/opensans/v17/mem5YaGs126MiZpBA-UN_r8OUuhs.ttf',
            'https://fonts.gstatic.com/s/opensans/v17/mem8YaGs126MiZpBA-UFVZ0e.ttf',
        }

        self.assertEqual(found_uris, expected_uris)

        expected_messages = '''
        Dispatching "click" on CSS selector "!document"
        Dispatching "click" on CSS selector ".ScrollableContainer__editButton___1g8v9"
        The JS crawler found a total of 2 event listeners
        '''

        found, not_found = self._log_contains(expected_messages)
        self.assertEqual(not_found, [])

    def test_react_icons_menu(self):
        url = 'https://react-icons-kit.now.sh/'
        found_uris = self._crawl(url)

        expected_url_regexes = {
            'https://api.github.com/repos/wmira/react-icons-kit',
            'https://buttons.github.io/buttons.js',
            'https://fonts.googleapis.com/css\\?family=Roboto',
            'https://react-icons-kit.now.sh/',
            'https://react-icons-kit.now.sh/static/css/main..*?.chunk.css',
            'https://react-icons-kit.now.sh/static/js/main..*?.chunk.js',
        }

        self._multi_regex_match(expected_url_regexes, found_uris)

        expected_messages = '''
        Dispatching "click" on CSS selector ".sc-hSdWYo div:nth-of-type(2)"
        Processing event 32 out of (unknown) for https://react-icons-kit.now.sh/.
        Event dispatch error count is 0.
        Already processed 35 events with types: {u'click': 35}
        Ignoring "click" event on selector
        '''

        found, not_found = self._log_contains(expected_messages)
        self.assertEqual(not_found, [])

    def test_react_button(self):
        url = 'https://84ol32ono9.csb.app/'
        found_uris = self._crawl(url)

        expected_url_regexes = {
            'https://84ol32ono9.csb.app/',
            'https://84ol32ono9.csb.app/babel-transpiler..*?.worker.js',
            'https://84ol32ono9.csb.app/frame.html\\?_sw-precache=.*?',
            'https://84ol32ono9.csb.app/sandbox-service-worker.js',
            'https://aiwi8rnkp5.execute-api.eu-west-1.amazonaws.com/prod/packages/babel-runtime.*?',
            'https://codesandbox.io/api/v1/sandboxes/84ol32ono9',
            'https://codesandbox.io/static/browserfs.*/browserfs.min.js',
            'https://codesandbox.io/static/js/babel..*?.min.js',
            'https://codesandbox.io/static/js/common-sandbox..*?.chunk.js',
            'https://codesandbox.io/static/js/default~app~embed~sandbox..*?.chunk.js',
            'https://codesandbox.io/static/js/sandbox..*?.js',
            'https://codesandbox.io/static/js/sandbox-startup..*?.js',
            'https://codesandbox.io/static/js/vendors~sandbox..*?.chunk.js',
            'https://d1jyvh0kxilfa7.cloudfront.net/v1/combinations/babel-runtime.*?.json'
        }

        self._multi_regex_match(expected_url_regexes, found_uris)

        expected_messages = '''
        Dispatching "click" on CSS selector "!document"
        Dispatching "click" on CSS selector "button"
        Chrome handled an alert dialog generated by the page
        Processing event 1 out of (unknown)
        Ignoring "click" event on selector "button"
        '''

        found, not_found = self._log_contains(expected_messages)
        self.assertEqual(not_found, [])

    def test_react_cart(self):
        #
        # Source code for this application lives at:
        #
        #   https://github.com/vishal2612200/react-shopping-cart
        #
        url = 'https://react-shopping-cart-67954.firebaseapp.com/'
        found_uris = self._crawl(url)

        expected_uris = {
            'https://api.github.com/repos/jeffersonRibeiro/react-shopping-cart',
            'https://buttons.github.io/buttons.js',
            'https://fonts.googleapis.com/css\\?family=Roboto',
            'https://fonts.gstatic.com/s/roboto/v20/KFOmCnqEu92Fr1Mu4mxP.ttf',
            'https://react-shopping-cart-67954.firebaseapp.com/',
            'https://react-shopping-cart-67954.firebaseapp.com/normalize.css',
            'https://react-shopping-cart-67954.firebaseapp.com/static/css/main..*.chunk.css',
            'https://react-shopping-cart-67954.firebaseapp.com/static/js/1..*.chunk.js',
            'https://react-shopping-cart-67954.firebaseapp.com/static/js/main..*.chunk.js',
            'https://react-shopping-cart-67954.firebaseio.com/products.json',
            'https://www.google-analytics.com/analytics.js',
            'https://www.googletagmanager.com/gtag/js\\?id=UA-85006284-3',
        }

        self._multi_regex_match(expected_uris, found_uris)

        expected_messages = '''
        Dispatching "click" on CSS selector ".filters .filters-available-size:nth-child(2) [type]"
        Dispatching "click" on CSS selector ".filters .filters-available-size:nth-child(4) label"
        '''

        found, not_found = self._log_contains(expected_messages)
        self.assertEqual(not_found, [])
