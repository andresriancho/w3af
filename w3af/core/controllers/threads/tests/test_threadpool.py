"""
test_threadpool.py

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

from w3af.core.controllers.threads.threadpool import Pool


def noop():
    return 1 + 2


def delay():
    time.sleep(0.5)
    return 0


class TestWorkerPool(unittest.TestCase):
    def test_exceptions(self):
        worker_pool = Pool(3, worker_names='WorkerThread')

        def raise_on_1(foo):
            if foo == 1:
                raise TypeError('%s Boom!' % foo)

            return foo

        answers = worker_pool.imap_unordered(raise_on_1, xrange(3))

        try:
            [i for i in answers]
        except TypeError, te:
            self.assertEqual(str(te), '1 Boom!')
            # pylint: disable=E1101
            self.assertIn("raise TypeError('%s Boom!' % foo)", te.original_traceback_string)

    def test_terminate_join_after_tasks(self):
        worker_pool = Pool(processes=4,
                           worker_names='WorkerThread',
                           maxtasksperchild=3)

        for _ in xrange(12):
            result = worker_pool.apply_async(func=noop)
            self.assertEqual(result.get(), 3)

        worker_pool.terminate_join()

    def test_get_pool_queue_sizes(self):
        worker_pool = Pool(processes=4,
                           worker_names='WorkerThread',
                           maxtasksperchild=3)

        for _ in xrange(12):
            worker_pool.apply_async(func=delay)

        pool_sizes = worker_pool.get_pool_queue_sizes()
        self.assertGreater(pool_sizes['inqueue_size'], 0)
        self.assertEqual(pool_sizes['outqueue_size'], 0)

        worker_pool.terminate_join()

    def test_output_pool_size(self):
        worker_pool = Pool(processes=4,
                           worker_names='WorkerThread',
                           maxtasksperchild=3)

        results = []

        for _ in xrange(12):
            result = worker_pool.apply_async(func=delay)
            results.append(result)

        pool_sizes = worker_pool.get_pool_queue_sizes()

        while pool_sizes['inqueue_size']:
            pool_sizes = worker_pool.get_pool_queue_sizes()

        # Give the result handler task inside the pool set the results on the
        # result instances stored in the results lists
        time.sleep(1)

        # There should be no pending tasks in the output queue
        self.assertEqual(pool_sizes['outqueue_size'], 0)

        worker_pool.terminate_join()

    def test_terminate_terminate(self):
        worker_pool = Pool(1, worker_names='WorkerThread')
        worker_pool.terminate()
        worker_pool.terminate()

    def test_close_terminate(self):
        worker_pool = Pool(1, worker_names='WorkerThread')
        worker_pool.close()
        worker_pool.terminate()

    def test_terminate_join(self):
        worker_pool = Pool(1, worker_names='WorkerThread')
        worker_pool.terminate()
        worker_pool.join()

    def test_decrease_number_of_workers(self):
        worker_pool = Pool(processes=4,
                           worker_names='WorkerThread',
                           maxtasksperchild=3)

        self.assertEqual(worker_pool.get_worker_count(), 4)

        for _ in xrange(12):
            result = worker_pool.apply_async(func=noop)
            self.assertEqual(result.get(), 3)

        self.assertEqual(worker_pool.get_worker_count(), 4)

        worker_pool.set_worker_count(1)

        # It takes some time...
        self.assertEqual(worker_pool.get_worker_count(), 4)

        for _ in xrange(12):
            result = worker_pool.apply_async(func=noop)
            self.assertEqual(result.get(), 3)

        self.assertEqual(worker_pool.get_worker_count(), 1)

        worker_pool.terminate()
        worker_pool.join()

    def test_increase_number_of_workers(self):
        worker_pool = Pool(processes=2,
                           worker_names='WorkerThread',
                           maxtasksperchild=3)

        self.assertEqual(worker_pool.get_worker_count(), 2)

        for _ in xrange(12):
            result = worker_pool.apply_async(func=noop)
            self.assertEqual(result.get(), 3)

        self.assertEqual(worker_pool.get_worker_count(), 2)

        worker_pool.set_worker_count(4)

        # Size increase is immediate
        self.assertEqual(worker_pool.get_worker_count(), 4)

        worker_pool.terminate()
        worker_pool.join()

    def test_change_number_of_workers_requirement(self):
        worker_pool = Pool(processes=2,
                           worker_names='WorkerThread')
        self.assertRaises(AssertionError, worker_pool.set_worker_count, 3)

    def test_worker_stats_idle(self):
        worker_pool = Pool(processes=1, worker_names='WorkerThread')
        func_name, func_args = worker_pool._pool[0].worker.get_real_func_name_args()
        self.assertIsNone(func_name)
        self.assertIsNone(func_args)
        self.assertTrue(worker_pool._pool[0].worker.is_idle())

    def test_worker_stats_not_idle(self):
        worker_pool = Pool(processes=1, worker_names='WorkerThread')

        def sleep(sleep_time, **kwargs):
            time.sleep(sleep_time)

        args = (2,)
        kwds = {'x': 2}
        worker_pool.apply_async(func=sleep, args=args, kwds=kwds)

        # Let the worker get the task
        time.sleep(0.3)

        func_name, func_args = worker_pool._pool[0].worker.get_real_func_name_args()
        # Got it?
        self.assertFalse(worker_pool._pool[0].worker.is_idle())
        self.assertEqual(func_name, 'sleep')
        self.assertEqual(func_args, args)
        self.assertEqual(worker_pool._pool[0].worker.kwargs, kwds)
        self.assertGreater(worker_pool._pool[0].worker.job, 1)

    def test_inspect_threads(self):
        worker_pool = Pool(processes=1, worker_names='WorkerThread')

        def sleep(sleep_time, **kwargs):
            time.sleep(sleep_time)

        args = (2,)
        kwds = {'x': 2}
        worker_pool.apply_async(func=sleep, args=args, kwds=kwds)

        # Let the worker get the task
        time.sleep(0.3)

        worker_states = worker_pool.inspect_threads()
        self.assertEqual(len(worker_states), 1)

        worker_state = worker_states[0]

        self.assertEqual(worker_state['func_name'], 'sleep')
        self.assertEqual(worker_state['args'], args)
        self.assertEqual(worker_state['kwargs'], kwds)
        self.assertEqual(worker_state['idle'], False)

    def test_max_queued_tasks(self):
        worker_pool = Pool(processes=1, max_queued_tasks=2)

        # These tasks should be queued very fast
        worker_pool.apply_async(func=time.sleep, args=(2,))
        worker_pool.apply_async(func=time.sleep, args=(2,))
        worker_pool.apply_async(func=time.sleep, args=(2,))
        worker_pool.apply_async(func=time.sleep, args=(2,))

        # Now the pool is full and we need to wait in the main
        # thread to get the task queued
        start = time.time()

        worker_pool.apply_async(func=time.sleep, args=(2,))

        spent = time.time() - start

        worker_pool.close()
        worker_pool.join()

        self.assertLess(spent, 2.1)
        self.assertGreater(spent, 1.9)
