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
            'http://react-hello-world-app.surge.sh/static/js/main.d78accb8.js',
            'http://react-hello-world-app.surge.sh/static/css/main.4b51051d.css',
            'http://react-hello-world-app.surge.sh/'
        }

        self.assertEqual(found_uris, expected_uris)

        # Note: These should be in order, the _log_contains method will take care of
        #       split() and strip() before searching for them in the log file
        expected_messages = '''
        Dispatching "click" on CSS selector "!document"
        Dispatching "click" on CSS selector ".AddGreeter button"
        Dispatching "click" on CSS selector ".HelloWorldList .HelloWorld:nth-of-type(2) button:nth-child(2)"
        Dispatching "click" on CSS selector ".HelloWorldList .HelloWorld:nth-of-type(2) button:nth-child(2) [role]"
        Dispatching "click" on CSS selector ".HelloWorldList .HelloWorld:nth-of-type(2) button:nth-child(3)"
        Dispatching "click" on CSS selector ".HelloWorldList .HelloWorld:nth-of-type(2) button:nth-child(3) [role]"
        Dispatching "click" on CSS selector ".HelloWorldList .HelloWorld:nth-of-type(2) button:nth-child(5)"
        Dispatching "click" on CSS selector ".HelloWorldList .HelloWorld:nth-of-type(2) button:nth-child(5) [role]"
        The JS crawler noticed a big change in the DOM.
        Dispatching "click" on CSS selector "!document"
        Dispatching "click" on CSS selector ".HelloWorldList .HelloWorld:nth-of-type(3) button:nth-child(2)"
        Dispatching "click" on CSS selector ".HelloWorldList .HelloWorld:nth-of-type(3) button:nth-child(2) [role]"
        Dispatching "click" on CSS selector ".HelloWorldList .HelloWorld:nth-of-type(3) button:nth-child(3)"
        Dispatching "click" on CSS selector ".HelloWorldList .HelloWorld:nth-of-type(3) button:nth-child(3) [role]"
        Dispatching "click" on CSS selector ".HelloWorldList .HelloWorld:nth-of-type(3) button:nth-child(5)"
        The JS crawler noticed a big change in the DOM.
        Dispatching "click" on CSS selector "!document"
        Dispatching "click" on CSS selector ".HelloWorldList .HelloWorld:nth-of-type(3) button:nth-child(5) [role]"
        Processing event 13 out of (unknown) for http://react-hello-world-app.surge.sh/. Event dispatch error count is 0. Already processed 16 events with types: {u'click': 35}
        The JS crawler noticed a big change in the DOM.
        '''

        found, not_found = self._log_contains(expected_messages)
        self.assertEqual(not_found, [])
