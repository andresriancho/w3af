import unittest

from w3af.core.controllers.threads.threadpool import Pool


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

        def noop():
            return 1 + 2

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

        def noop():
            return 1 + 2

        for _ in xrange(12):
            result = worker_pool.apply_async(func=noop)
            self.assertEqual(result.get(), 3)

        self.assertEqual(worker_pool.get_worker_count(), 2)

        worker_pool.set_worker_count(4)

        # It takes some time...
        self.assertEqual(worker_pool.get_worker_count(), 2)

        for _ in xrange(12):
            result = worker_pool.apply_async(func=noop)
            self.assertEqual(result.get(), 3)

        self.assertEqual(worker_pool.get_worker_count(), 4)

        worker_pool.terminate()
        worker_pool.join()

    def test_change_number_of_workers_requirement(self):
        worker_pool = Pool(processes=2,
                           worker_names='WorkerThread')
        self.assertRaises(AssertionError, worker_pool.set_worker_count, 3)
