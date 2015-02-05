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