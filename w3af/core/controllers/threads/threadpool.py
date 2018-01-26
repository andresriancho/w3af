"""
threadpool.py

Copyright 2006 Andres Riancho

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
import threading
import Queue
import time

from functools import partial

from multiprocessing.dummy import Process, current_process
from multiprocessing.util import Finalize, debug
from multiprocessing import cpu_count

from .pool276 import ThreadPool, RUN

from w3af.core.data.misc.smart_queue import SmartQueue

__all__ = ['Pool']


class one_to_many(object):
    """
    This is a simple wrapper that translates one argument to many in a function
    call. Useful for passing to the threadpool map function.
    """
    def __init__(self, func):
        self.func = func

        # Similar to functools wraps
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __call__(self, args):
        return self.func(*args)


class return_args(object):
    """
    Utility function that returns the args in the result, useful when calling
    functions like imap_unordered().
    """
    def __init__(self, func, *args, **kwds):
        self.func = partial(func, *args, **kwds)

    def __call__(self, *args, **kwds):
        return args, self.func(*args, **kwds)


class DaemonProcess(Process):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super(DaemonProcess, self).__init__(group, target, name, args, kwargs)
        self.daemon = True

    def start(self):
        """
        This is a race condition in DaemonProcess.start() which was found
        during some of the test scans I run. The race condition exists
        because we're using Threads for a Pool that was designed to be
        used with real processes: thus there is no worker.exitcode,
        thus it has to be simulated in a race condition-prone way.

        I'm overriding this method in order to move this line:

            self._start_called = True

        Closer to the call to .start(), which should reduce the chances
        of triggering the race conditions by 1% ;-)
        """
        assert self._parent is current_process()

        if hasattr(self._parent, '_children'):
            self._parent._children[self] = None

        self._start_called = True
        threading.Thread.start(self)


class Pool(ThreadPool):

    def __init__(self, processes=None, initializer=None, initargs=(),
                 worker_names=None, maxtasksperchild=None,
                 max_queued_tasks=0):
        """
        Overriding this method in order to:
            * Name the pool worker threads
            * Name the threads used for managing the Pool internals
        """
        self.Process = partial(DaemonProcess, name=worker_names)

        self.worker_names = worker_names
        self._setup_queues(max_queued_tasks)
        self._taskqueue = Queue.Queue()
        self._cache = {}
        self._state = RUN
        self._maxtasksperchild = maxtasksperchild
        self._initializer = initializer
        self._initargs = initargs

        if processes is None:
            try:
                processes = cpu_count()
            except NotImplementedError:
                processes = 1
        if processes < 1:
            raise ValueError("Number of processes must be at least 1")

        if initializer is not None and not hasattr(initializer, '__call__'):
            raise TypeError('initializer must be a callable')

        self._processes = processes
        self._pool = []
        self._repopulate_pool()

        self._worker_handler = threading.Thread(
            target=Pool._handle_workers,
            args=(self, ),
            name='PoolWorkerHandler')
        self._worker_handler.daemon = True
        self._worker_handler._state = RUN
        self._worker_handler.start()

        self._task_handler = threading.Thread(
            target=Pool._handle_tasks,
            args=(self._taskqueue, self._quick_put, self._outqueue,
                  self._pool, self._cache),
            name='PoolTaskHandler')
        self._task_handler.daemon = True
        self._task_handler._state = RUN
        self._task_handler.start()

        self._result_handler = threading.Thread(
            target=Pool._handle_results,
            args=(self._outqueue, self._quick_get, self._cache),
            name='PoolResultHandler')
        self._result_handler.daemon = True
        self._result_handler._state = RUN
        self._result_handler.start()

        self._terminate = Finalize(
            self, self._terminate_pool,
            args=(self._taskqueue, self._inqueue, self._outqueue, self._pool,
                  self._worker_handler, self._task_handler,
                  self._result_handler, self._cache),
            exitpriority=15)

    def get_worker_count(self):
        return len(self._pool)

    def set_worker_count(self, count):
        """
        Set the number of workers.

        Keep in mind that this is not an immediate when decreasing
        the pool process count!

            * When increasing the size, the threadpool will call
              repopulate_pool() and the new threads will be created

            * When decreasing the size, a thread will finish because
              of maxtasksperchild, then repopulate_pool() will be
              called async and the thread will *not* be created,
              thus decreasing the pool size

        The change is made effective depending on the work load and
        the time required to finish each task.

        :param count: The new process count
        :return: None
        """
        assert self._maxtasksperchild, 'Can only adjust size if maxtasksperchild is set'
        assert count >= 1, 'Number of processes must be at least 1'
        self._processes = count
        self._repopulate_pool()

    def _setup_queues(self, max_queued_tasks):
        #self._inqueue = SmartQueue(maxsize=max_queued_tasks, name=self.worker_names)
        self._inqueue = Queue.Queue(maxsize=max_queued_tasks)
        self._outqueue = Queue.Queue()
        self._quick_put = self._inqueue.put
        self._quick_get = self._outqueue.get

    def map_multi_args(self, func, iterable, chunksize=None):
        """
        Blocks until all results are done (please note the .get())
        """
        assert self._state == RUN
        return self.map_async(one_to_many(func), iterable, chunksize).get()

    def in_qsize(self):
        return self._taskqueue.qsize()

    def is_running(self):
        return self._state == RUN

    def terminate_join(self):
        self.terminate()
        self.join()

    def _join_exited_workers(self):
        """Cleanup after any worker processes which have exited due to reaching
        their specified lifetime.  Returns True if any workers were cleaned up.
        """
        cleaned = False
        for i in reversed(range(len(self._pool))):
            worker = self._pool[i]
            if worker.exitcode is not None:
                # worker exited
                try:
                    worker.join()
                except RuntimeError:
                    #
                    # RuntimeError: cannot join thread before it is started
                    #
                    # This is a race condition in DaemonProcess.start() which was found
                    # during some of the test scans I run. The race condition exists
                    # because we're using Threads for a Pool that was designed to be
                    # used with real processes: thus there is no worker.exitcode,
                    # thus it has to be simulated in a race condition-prone way.
                    #
                    continue
                else:
                    debug('cleaning up worker %d' % i)
                cleaned = True
                del self._pool[i]
        return cleaned

    def finish(self, timeout=120):
        """
        Wait until all tasks in the self._inqueue have been processed (the queue
        has size == 0) and then call terminate on the Pool.

        I know this is not the best way of doing it, but had some dead-lock
        issues with:

            self.close()
            self.join()

        :param timeout: Wait up to timeout seconds for the queues to be empty
        """
        delay = 0.1

        for _ in xrange(int(timeout / delay)):
            if (self._inqueue.qsize() == 0 and
                self._outqueue.qsize() == 0 and
                self._taskqueue.qsize() == 0):
                break

            time.sleep(delay)

        self.terminate()
        self.join()

