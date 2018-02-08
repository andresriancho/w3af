"""
test_pebble_limit_memory_usage.py

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
import unittest
import time

from pebble import ProcessPool
from w3af.core.data.parsers.mp_document_parser import limit_memory_usage


def just_sleep(secs):
    time.sleep(secs)
    return secs


def use_memory_in_string(memory):
    block_size = 1024
    memory_user = ''

    for _ in xrange(int(memory / block_size)):
        memory_user += block_size * 'A'

    return len(memory_user)


class TestPebbleMemoryUsage(unittest.TestCase):

    # From the current virtual memory used by the process, we allow the
    # sub-processes (which have the same virtual memory because they are forks)
    # to grow 8 MB more:
    MEMORY_LIMIT = 1024 * 1024 * 8

    def test_sub_process_with_low_memory_usage_not_affected(self):
        #
        # Run three tasks that don't require any memory and make sure that
        # everything runs as expected
        #
        pool = self.get_pool_with_memlimit()

        results = []
        secs = 1

        for _ in xrange(4):
            future = pool.schedule(just_sleep, args=(secs,))
            results.append(future)

        for future in results:
            self.assertEqual(future.result(), secs)

    def test_sub_process_with_high_memory_usage_but_not_so_much_is_not_killed(self):
        #
        # Run a task that requires a lot of memory but doesn't trigger the limit
        # The process shouldn't die
        #
        pool = self.get_pool_with_memlimit()

        # Run this to init the pool
        pool.schedule(just_sleep, args=(0.1,))

        # Get the worker pids
        workers_before_test = pool._pool_manager.worker_manager.workers.keys()[:]

        usage = self.MEMORY_LIMIT / 2.0
        future = pool.schedule(use_memory_in_string, args=(usage,))

        self.assertEqual(future.result(), usage)
        self.assertEqual(workers_before_test, pool._pool_manager.worker_manager.workers.keys()[:])

    def test_effective_kill_limit(self):
        #
        # This started as a tool to let me know when the process is killed.
        # It increases the memory usage by 10k on each test until it finds the
        # limit.
        #
        # It makes sense that the limit set in resource.setrlimit is not exactly equal to
        # the memory I consume since there is process overhead (the python VM). See
        # how the real limit is calculated in get_real_limit().
        #
        pool = self.get_pool_with_memlimit()

        block_size = 1024 * 10
        current_len = 0

        while True:
            current_len += block_size
            future = pool.schedule(use_memory_in_string, args=(current_len,))
            try:
                future.result()
            except MemoryError:
                print('Limit found at %s bytes' % current_len)
                break

        #self.assertGreaterEqual(self.MEMORY_LIMIT * 1.2, current_len)
        #self.assertLessEqual(self.MEMORY_LIMIT * 0.8, current_len)

    def test_sub_process_with_high_memory_usage_is_killed(self):
        #
        # Run a task that requires a lot of memory. Confirm that the process
        # is killed by the OS. Confirm that pebble starts a new process and
        # leaves the pool in an usable state for running other tasks
        #
        pool = self.get_pool_with_memlimit()

        # Run this to init the pool
        pool.schedule(just_sleep, args=(0.1,))

        # Get the worker pids
        workers_before_test = pool._pool_manager.worker_manager.workers.keys()[:]

        usage = self.MEMORY_LIMIT * 5.0
        future = pool.schedule(use_memory_in_string, args=(usage,))

        # When the memory limit is reached, the process raises MemoryError
        self.assertRaises(MemoryError, future.result)

        # Things should just work as usual after the MemoryError exception
        results = []
        secs = 1

        for _ in xrange(4):
            future = pool.schedule(just_sleep, args=(secs,))
            results.append(future)

        for future in results:
            self.assertEqual(future.result(), secs)

        self.assertEqual(workers_before_test, pool._pool_manager.worker_manager.workers.keys()[:])

    def test_main_process_high_memory_usage_after_starting_nothing_killed(self):
        #
        # Run a task that sleeps for a while and start consuming a lot of
        # memory in the MAIN process. Assert that the main process is not
        # killed, assert that the child process is not killed.
        #
        pool = self.get_pool_with_memlimit()
        results = []
        secs = 5

        for _ in xrange(4):
            future = pool.schedule(just_sleep, args=(secs,))
            results.append(future)

        # Use a lot of memory in the parent process
        use_memory_in_string(self.MEMORY_LIMIT * 2.0)

        # Get all the results, none should be a MemoryError
        for future in results:
            self.assertEqual(future.result(), secs)

    def test_main_process_high_memory_usage_before_starting_nothing_killed(self):
        #
        # Consume a lot of memory in the MAIN process, and then run a task in
        # pebble pool that sleeps for a while. Assert that the main process is
        # not killed, assert that the child process is not killed.
        #

        # Use a lot of memory in the parent process
        block_size = 1024
        memory_user = ''

        for _ in xrange(int(self.MEMORY_LIMIT * 2.0 / block_size)):
            memory_user += block_size * 'A'

        # Now do the pool stuff
        pool = self.get_pool_with_memlimit()
        results = []
        secs = 5

        for _ in xrange(4):
            future = pool.schedule(just_sleep, args=(secs,))
            results.append(future)

        # Get all the results, none should be a MemoryError
        for future in results:
            self.assertEqual(future.result(), secs)

    def get_pool_with_memlimit(self):
        pool = ProcessPool(initializer=limit_memory_usage,
                           initargs=[self.MEMORY_LIMIT],
                           max_workers=3)
        return pool
