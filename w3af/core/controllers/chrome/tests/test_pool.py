"""
test_pool.py

Copyright 2018 Andres Riancho

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
import Queue
import unittest

from w3af.core.controllers.chrome.pool import ChromePool, PoolInstrumentedChrome, ChromePoolException
from w3af.core.data.url.extended_urllib import ExtendedUrllib


class TestChromePool(unittest.TestCase):

    def setUp(self):
        self.uri_opener = ExtendedUrllib()
        self.http_traffic_queue = Queue.Queue()
        self.http_traffic_queue.debugging_id = 'abcd1234'

        self.pool = ChromePool(self.uri_opener,
                               max_instances=2)

    def tearDown(self):
        self.pool.terminate()

    def test_get_new_chrome_pool_empty(self):
        chrome = self.pool.get(self.http_traffic_queue)
        self.assertIsInstance(chrome, PoolInstrumentedChrome)

    def test_get_new_chrome_pool_with_free_instance(self):
        chrome_1 = self.pool.get(self.http_traffic_queue)
        self.pool.free(chrome_1)

        chrome_2 = self.pool.get(self.http_traffic_queue)
        self.assertIs(chrome_1, chrome_2)

    def test_get_new_chrome_pool_full(self):
        self.pool.get(self.http_traffic_queue)
        self.pool.get(self.http_traffic_queue)

        self.assertRaises(ChromePoolException,
                          self.pool.get,
                          self.http_traffic_queue,
                          timeout=1)

    def test_free(self):
        chrome = self.pool.get(self.http_traffic_queue)
        self.pool.free(chrome)

        self.assertIn(chrome, self.pool._free)
        self.assertNotIn(chrome, self.pool._in_use)

    def test_remove(self):
        chrome = self.pool.get(self.http_traffic_queue)
        self.pool.remove(chrome)

        self.assertNotIn(chrome, self.pool._free)
        self.assertNotIn(chrome, self.pool._in_use)

    def test_free_triggers_max_tasks(self):
        for _ in xrange(self.pool.MAX_TASKS):
            chrome = self.pool.get(self.http_traffic_queue)
            self.pool.free(chrome)
            self.assertIn(chrome, self.pool._free)

        # This time should trigger the removal of the instance from the pool
        chrome = self.pool.get(self.http_traffic_queue)
        self.pool.free(chrome)

        self.assertNotIn(chrome, self.pool._free)
        self.assertNotIn(chrome, self.pool._in_use)
