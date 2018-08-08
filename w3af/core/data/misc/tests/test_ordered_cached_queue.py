"""
test_ordered_cached_queue.py

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
import time
import unittest
import threading

from w3af.core.data.misc.ordered_cached_queue import OrderedCachedQueue
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.dc.generic.kv_container import KeyValueContainer
from w3af.core.data.dc.headers import Headers


class TestOrderedCachedQueue(unittest.TestCase):

    def test_put_none_then_fuzzable_request(self):
        q = OrderedCachedQueue(maxsize=2)

        q.put(None)
        q.put(create_simple_fuzzable_request(1))

        # Reads the fuzzable request
        q.get()

        # Reads the None
        self.assertIsNone(q.get())

    def test_put_none_after_fuzzable_request(self):
        q = OrderedCachedQueue(maxsize=2)

        q.put(create_simple_fuzzable_request(1))
        q.put(None)

        # Reads the fuzzable request
        q.get()

        # Reads the None
        self.assertIsNone(q.get())

    def test_put_same_fuzzable_request_twice(self):
        q = OrderedCachedQueue(maxsize=2)

        q.put(create_simple_fuzzable_request(1))
        q.put(create_simple_fuzzable_request(1))

        self.assertEqual(q.get(), q.get())

    def test_read_in_order(self):
        q = OrderedCachedQueue(maxsize=2)
        hash_list = []

        for i in xrange(5):
            fr = create_simple_fuzzable_request(i)
            hash_list.append(fr.get_hash())
            q.put(fr)

        unordered_hash_list = hash_list[:]
        hash_list.sort()

        self.assertNotEqual(unordered_hash_list, hash_list)

        for i in xrange(4):
            fr = q.get()
            self.assertEqual(fr.get_hash(), hash_list[i])

    def test_prefer_memory_over_disk(self):
        q = OrderedCachedQueue(maxsize=2)

        # These two go to the in memory queue
        q.put(create_simple_fuzzable_request(1))
        q.put(create_simple_fuzzable_request(2))

        # This one goes to the disk queue
        q.put(create_simple_fuzzable_request(3))

        # Read one from memory
        q.get()
        self.assertEqual(len(q.memory), 1)
        self.assertEqual(len(q.disk), 1)

        # Write one to memory
        q.put(create_simple_fuzzable_request(3))
        self.assertEqual(len(q.memory), 2)
        self.assertEqual(len(q.disk), 1)

    def test_add_exceed_memory(self):
        q = OrderedCachedQueue(maxsize=2)

        # These two go to the in memory queue
        q.put(create_simple_fuzzable_request(1))
        q.put(create_simple_fuzzable_request(2))

        self.assertEqual(q.qsize(), 2)
        self.assertEqual(len(q.memory), 2)

        # This one goes to the disk queue
        q.put(create_simple_fuzzable_request(3))

        self.assertEqual(q.qsize(), 3)
        self.assertEqual(len(q.memory), 2)
        self.assertEqual(len(q.disk), 1)

        # Get all
        self.assertEqual(read_fuzzable_request_parameter(q.get()), 1)

        self.assertEqual(len(q.memory), 1)
        self.assertEqual(len(q.disk), 1)

        self.assertEqual(read_fuzzable_request_parameter(q.get()), 2)

        self.assertEqual(len(q.memory), 0)
        self.assertEqual(len(q.disk), 1)

        self.assertEqual(read_fuzzable_request_parameter(q.get()), 3)

        self.assertEqual(len(q.memory), 0)
        self.assertEqual(len(q.disk), 0)

        self.assertEqual(q.qsize(), 0)

    def test_exceptions_no_fail_sync_pointer(self):
        q = OrderedCachedQueue(maxsize=2)
        q.put(create_simple_fuzzable_request(1))
        q.get()

        self.assertRaises(Exception, q.get, block=False)

        q.put(create_simple_fuzzable_request(1))
        self.assertEquals(read_fuzzable_request_parameter(q.get()), 1)

    def test_simple_rpm_speed(self):
        q = OrderedCachedQueue()

        self.assertEqual(0.0, q.get_input_rpm())
        self.assertEqual(0.0, q.get_output_rpm())

        for i in xrange(4):
            q.put(create_simple_fuzzable_request(i))
            # 20 RPM
            time.sleep(3)

        self.assertEqual(q.qsize(), 4)

        self.assertGreater(q.get_input_rpm(), 19)
        self.assertLess(q.get_input_rpm(), 20)

        for i in xrange(4):
            q.get()
            # 60 RPM
            time.sleep(1)

        self.assertGreater(q.get_output_rpm(), 59)
        self.assertLess(q.get_output_rpm(), 60)
        self.assertEqual(q.qsize(), 0)

    def test_join_memory(self):
        q = OrderedCachedQueue(maxsize=2)
        q.put(create_simple_fuzzable_request(1))

        def queue_get_after_delay(queue):
            time.sleep(1)
            queue.get()
            queue.task_done()

        t = threading.Thread(target=queue_get_after_delay,
                             args=(q,))
        t.start()

        start = time.time()

        # This should take 1 second
        q.join()

        spent = time.time() - start

        self.assertGreater(spent, 1)

    def test_join_memory_and_disk(self):
        q = OrderedCachedQueue(maxsize=2)
        for x in range(10):
            q.put(create_simple_fuzzable_request(x))

        def queue_get_after_delay(queue):
            time.sleep(1)

            for x in range(2):
                queue.get()
                queue.task_done()

            time.sleep(1)

            for x in range(8):
                queue.get()
                queue.task_done()

        t = threading.Thread(target=queue_get_after_delay,
                             args=(q,))
        t.start()

        start = time.time()

        # This should take 3 seconds
        q.join()

        spent = time.time() - start

        self.assertGreater(spent, 2)


def create_simple_fuzzable_request(unique_id):
    unique_id = str(unique_id)

    url = URL('http://w3af.com/')
    headers = Headers([(u'Hello', u'World')])
    post_data = KeyValueContainer(init_val=[('a', [unique_id])])

    return FuzzableRequest(url,
                           method='GET',
                           post_data=post_data,
                           headers=headers)


def read_fuzzable_request_parameter(fuzzable_request):
    value = fuzzable_request.get_raw_data()['a'][0]
    value = int(value)
    return value
