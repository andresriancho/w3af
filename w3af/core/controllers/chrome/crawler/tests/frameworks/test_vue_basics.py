"""
test_vue_basics.py

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
    def test_vue_todo_list(self):
        url = 'http://vue-todo-test.surge.sh'
        found_uris = self._crawl(url)

        expected_uris = {
            'http://vue-todo-test.surge.sh/static/js/app.fbc4d9791175d472758c.js',
            'https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css',
            'http://vue-todo-test.surge.sh/static/js/vendor.522563e38c6b6cbc0cd5.js',
            'http://vue-todo-test.surge.sh/static/css/app.1477e86b9d088130e2257d5ba96f7893.css',
            'http://vue-todo-test.surge.sh/static/js/manifest.2ae2e69a05c33dfc65f8.js',
            'http://vue-todo-test.surge.sh/'
        }

        self.assertEqual(found_uris, expected_uris)

        expected_messages = '''
        The JS crawler found a total of 0 event listeners
        '''

        found, not_found = self._log_contains(expected_messages)
        self.assertEqual(not_found, [])
