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
import resource
import time

from pebble import ProcessPool


def just_sleep(secs):
    time.sleep(secs)
    return secs


def use_memory_in_string(memory):
    block_size = 256
    memory_user = ''

    for _ in xrange(int(memory / block_size)):
        memory_user += 256 * 'A'

    return len(memory_user)


class TestPebbleMemoryUsage(unittest.TestCase):

    MEMORY_LIMIT = 67108864

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

        usage = self.MEMORY_LIMIT / 16
        future = pool.schedule(use_memory_in_string, args=(usage,))

        self.assertEqual(future.result(), usage)
        self.assertEqual(workers_before_test, pool._pool_manager.worker_manager.workers.keys()[:])

    def test_effective_kill_limit(self):
        #
        # This is just a tool to let me know when the process is killed. It increases the
        # memory usage by 10k on each test until it finds the limit.
        #
        # It makes sense that the limit set in resource.setrlimit is not exactly equal to
        # the memory I consume since there is process overhead
        #
        pool = self.get_pool_with_memlimit()

        block_size = 10000
        current_len = 0

        while True:
            current_len += block_size
            future = pool.schedule(use_memory_in_string, args=(current_len,))
            try:
                future.result()
            except MemoryError:
                print('Limit found at %s bytes' % current_len)
                break

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

        usage = self.MEMORY_LIMIT
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
        use_memory_in_string(self.MEMORY_LIMIT)

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
        block_size = 256
        memory_user = ''

        for _ in xrange(int(self.MEMORY_LIMIT / block_size)):
            memory_user += 256 * 'A'

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

        def initializer(memlimit):
            """
            Set the soft memory limit for the worker process.

            Retrieve current limits, re-use the hard limit.
            """
            if hasattr(resource, 'RLIMIT_AS'):
                # This works on Linux
                soft, hard = resource.getrlimit(resource.RLIMIT_AS)
                resource.setrlimit(resource.RLIMIT_AS, (memlimit, hard))
            elif hasattr(resource, 'RLIMIT_VMEM'):
                # This works on other OS (Mac)
                soft, hard = resource.getrlimit(resource.RLIMIT_VMEM)
                resource.setrlimit(resource.RLIMIT_VMEM, (memlimit, hard))
            else:
                print('w3af was unable to limit the resource usage of parser processes.')

        # 64 Mb of limit per each process
        pool = ProcessPool(initializer=initializer,
                           initargs=[self.MEMORY_LIMIT],
                           max_workers=3)
        return pool
