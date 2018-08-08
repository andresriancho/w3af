"""
test_cached_queue.py

Copyright 2017 Andres Riancho

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
import threading
import time

from w3af.core.data.misc.cached_queue import CachedQueue


class TestCachedQueue(unittest.TestCase):

    def test_prefer_memory_over_disk(self):
        q = CachedQueue(maxsize=2)

        # These two go to the in memory queue
        q.put(1)
        q.put(2)

        # This one goes to the disk queue
        q.put(3)

        # Read one from memory
        q.get()
        self.assertEqual(len(q.memory), 1)
        self.assertEqual(len(q.disk), 1)

        # Write one to memory
        q.put(4)
        self.assertEqual(len(q.memory), 2)
        self.assertEqual(len(q.disk), 1)

    def test_add_exceed_memory(self):
        q = CachedQueue(maxsize=2)

        # These two go to the in memory queue
        q.put(1)
        q.put(2)

        self.assertEqual(q.qsize(), 2)
        self.assertEqual(len(q.memory), 2)

        # This one goes to the disk queue
        q.put(3)

        self.assertEqual(q.qsize(), 3)
        self.assertEqual(len(q.memory), 2)
        self.assertEqual(len(q.disk), 1)

        # Get all
        self.assertEqual(q.get(), 1)

        self.assertEqual(len(q.memory), 1)
        self.assertEqual(len(q.disk), 1)

        self.assertEqual(q.get(), 2)

        self.assertEqual(len(q.memory), 0)
        self.assertEqual(len(q.disk), 1)

        self.assertEqual(q.get(), 3)

        self.assertEqual(len(q.memory), 0)
        self.assertEqual(len(q.disk), 0)

        self.assertEqual(q.qsize(), 0)

    def test_exceptions_no_fail_sync_pointer(self):
        q = CachedQueue(maxsize=2)
        q.put(1)
        q.get()

        self.assertRaises(Exception, q.get, block=False)

        q.put(1)
        self.assertEquals(q.get(), 1)

    def test_simple_rpm_speed(self):
        q = CachedQueue()

        self.assertEqual(0.0, q.get_input_rpm())
        self.assertEqual(0.0, q.get_output_rpm())

        for i in xrange(4):
            q.put(i)
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
        q = CachedQueue(maxsize=2)
        q.put(1)

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
        q = CachedQueue(maxsize=2)
        for x in range(10):
            q.put(x)

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
