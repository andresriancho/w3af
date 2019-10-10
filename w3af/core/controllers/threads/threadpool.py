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
import sys
import time
import Queue
import threading
import traceback

from functools import partial

from multiprocessing.dummy import Process, current_process
from multiprocessing.util import Finalize, debug
from multiprocessing import cpu_count

from .pool276 import ThreadPool, RUN, create_detailed_pickling_error, mapstar

from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.controllers.threads.decorators import apply_with_return_error

__all__ = ['Pool', 'return_args', 'one_to_many']


class one_to_many(object):
    """
    This is a simple wrapper that translates one argument to many in a function
    call. Useful for passing to the threadpool map function.
    """
    def __init__(self, func):
        self.func_orig = func

        # Similar to functools wraps
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __call__(self, args):
        return self.func_orig(*args)


class return_args(object):
    """
    Utility function that returns the args in the result, useful when calling
    functions like imap_unordered().
    """
    def __init__(self, func, *args, **kwds):
        self.func = partial(func, *args, **kwds)

        # Similar to functools wraps
        self.func_orig = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __call__(self, *args, **kwds):
        return args, self.func(*args, **kwds)


class DaemonProcess(Process):

    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super(DaemonProcess, self).__init__(group, target, name, args, kwargs)
        self.daemon = True
        self.worker = target
        self.name = name

    def get_state(self):
        state = self.worker.get_state()
        state['name'] = self.name
        return state

    def is_idle(self):
        return self.worker.is_idle()

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


def add_traceback_string(_exception):
    """
    Add the traceback string as a new attribute to the exception raised
    by the target function defined by the developer.

    Adding this original traceback allows us to better understand the
    root cause for exceptions that happen in functions which are run inside
    the Pool (most).

    For example, this is an exception stored in a /tmp/w3af-crash file before
    this patch:

        A "TypeError" exception was found while running crawl.phpinfo on "Method: GET | http://domain/".
        The exception was: "unsupported operand type(s) for -: 'float' and 'NoneType'" at pool276.py:get():643.
        The full traceback is:

          File "/home/user/tools/w3af/w3af/core/controllers/core_helpers/consumers/crawl_infrastructure.py", line 533, in _discover_worker
            result = plugin.discover_wrapper(fuzzable_request)
          File "/home/user/tools/w3af/w3af/core/controllers/plugins/crawl_plugin.py", line 53, in crawl_wrapper
            return self.crawl(fuzzable_request_copy)
          File "/home/user/tools/w3af/w3af/plugins/crawl/phpinfo.py", line 148, in crawl
            self.worker_pool.map_multi_args(self._check_and_analyze, args)
          File "/home/user/tools/w3af/w3af/core/controllers/threads/threadpool.py", line 430, in map_multi_args
            return self.map_async(one_to_many(func), iterable, chunksize).get()
          File "/home/user/tools/w3af/w3af/core/controllers/threads/pool276.py", line 643, in get
            raise self._value

    And after adding the original traceback and using it in exception_handler.py:

        A "TypeError" exception was found while running crawl.phpinfo on "Method: GET | http://domain/".
        The exception was: "unsupported operand type(s) for -: 'float' and 'NoneType'" at pool276.py:get():643.
        The full traceback is:

        Traceback (most recent call last):
          File "/home/user/tools/w3af/w3af/core/controllers/threads/threadpool.py", line 238, in __call__
            result = (True, func(*args, **kwds))
          File "/home/user/tools/w3af/w3af/core/controllers/threads/pool276.py", line 67, in mapstar
            return map(*args)
          File "/home/user/tools/w3af/w3af/core/controllers/threads/threadpool.py", line 55, in __call__
            return self.func_orig(*args)
          File "/home/user/tools/w3af/w3af/plugins/crawl/phpinfo.py", line 180, in _check_and_analyze
            1.0 - None
        TypeError: unsupported operand type(s) for -: 'float' and 'NoneType'

    The exact line where the exception is raised is shown!

    Adding new attributes to instances is not something I like, but in
    this case I had no choice...

    Creating a new Exception type and wrapping all exceptions generated
    by the pool with that one wouldn't work: we lose the exception type
    and can't do:

        try:
            ...
        except TypeError:
            ...

    The code for the whole framework would need to be changed to something
    like:

        try:
            ...
        except PoolException, pe:
            if isinstance(pe.original_exception, TypeError):
                ...

    :param _exception: The exception instance where to add the new attribute
    :return: None
    """
    except_type, except_class, tb = sys.exc_info()

    tb = traceback.format_exception(type(_exception), _exception, tb)
    _exception.original_traceback_string = ''.join(tb)


class Worker(object):

    __slots__ = ('func', 'args', 'kwargs', 'start_time', 'job', 'id')

    def __init__(self):
        self.func = None
        self.args = None
        self.kwargs = None
        self.start_time = None
        self.job = None
        self.id = rand_alnum(8)

    def is_idle(self):
        return self.func is None

    def get_real_func_name_args(self):
        """
        Because of various levels of abstraction the function name is not always in
        self.func.__name__, this method "unwraps" the abstractions and shows us
        something easier to digest.

        :return: The function name
        """

        # self.func/self.args could change over the execution of this method, so take
        # a copy here.
        current_func = self.func
        current_args = self.args

        if current_func is mapstar:
            current_func = current_args[0][0]
            current_args = current_args[0][1:]

        if current_func is apply_with_return_error:
            current_func = current_args[0][0]
            current_args = current_args[0][1:]

        if isinstance(current_func, return_args):
            return current_func.func_orig.__name__, current_args

        if isinstance(current_func, one_to_many):
            return current_func.func_orig.__name__, current_args

        if current_func is None:
            return None, None

        return current_func.__name__, current_args

    def get_state(self):
        func_name, func_args = self.get_real_func_name_args()

        return {'func_name': func_name,
                'args': func_args,
                'kwargs': self.kwargs,
                'start_time': self.start_time,
                'idle': self.is_idle(),
                'job': self.job,
                'worker_id': self.id}

    def __call__(self, inqueue, outqueue, initializer=None, initargs=(), maxtasks=None):
        assert maxtasks is None or (type(maxtasks) in (int, long) and maxtasks > 0)

        put = outqueue.put
        get = inqueue.get
        if hasattr(inqueue, '_writer'):
            inqueue._writer.close()
            outqueue._reader.close()

        if initializer is not None:
            initializer(*initargs)

        completed = 0
        while maxtasks is None or (maxtasks and completed < maxtasks):
            try:
                task = get()
            except (EOFError, IOError):
                debug('worker got EOFError or IOError -- exiting')
                break

            if task is None:
                debug('worker got sentinel -- exiting')
                break

            job, i, func, args, kwds = task

            # Tracking
            self.func = func
            self.args = args
            self.kwargs = kwds
            self.start_time = time.time()
            self.job = job

            try:
                result = (True, func(*args, **kwds))
            except Exception, e:
                add_traceback_string(e)
                result = (False, e)

            # Tracking
            self.func = None
            self.args = None
            self.kwargs = None
            self.start_time = None
            self.job = None

            try:
                put((job, i, result))
            except Exception as e:
                wrapped = create_detailed_pickling_error(e, result[1])
                put((job, i, (False, wrapped)))
            finally:
                # https://bugs.python.org/issue29861
                task = None
                job = None
                result = None
                func = None
                args = None
                kwds = None

                completed += 1

        debug('worker exiting after %d tasks' % completed)


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

        # Setting the max number of queued tasks for the ThreadPool is not
        # as simple as it looks.
        #
        # First I tried to limit the max size of self._inqueue (defined
        # in _setup_queues), that didn't work.
        #
        # Then I tried to limit the size for self._taskqueue, that didn't
        # work either.
        #
        # I had to set the maxsize of self._taskqueue to 1 and use the
        # max_queued_tasks parameter to limit the size of self._inqueue
        # This is required due to the ThreadPool internals, see the
        # definition of the _handle_tasks method in pool276.py where
        # the function is reading from self._taskqueue and writing to
        # self._inqueue.
        #
        # Not setting the limit in self._taskqueue allows the main thread
        # to enqueue an infinite number of tasks.
        #
        # Only setting the limit in self._taskqueue will not work, since
        # the _handle_tasks method is always reading from that queue
        # (which decreases its size) and writing to self._inqueue. Because
        # of those reads to self._taskqueue, the queue never reaches the
        # limit.
        #
        if max_queued_tasks != 0:
            assert max_queued_tasks - 1 > 0, 'max_queued_tasks needs to be at least 2'

        self._setup_queues(max_queued_tasks - 1)
        self._taskqueue = Queue.Queue(maxsize=1)

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

    def get_inqueue(self):
        return self._inqueue

    def get_outqueue(self):
        return self._outqueue

    def get_running_task_count(self):
        # Cheating here a little bit because the task queued in _inqueue will
        # eventually be run by the pool, but is not yet in the pool
        running_tasks = self._inqueue.qsize()

        for process in self._pool[:]:
            if not process.is_idle():
                running_tasks += 1

        return running_tasks

    def _repopulate_pool(self):
        """
        Bring the number of pool processes up to the specified number,
        for use after reaping workers which have exited.

        I overwrite this in order to change the Process target to a Worker
        object (instead of a function) in order to keep better stats of
        what it is doing.
        """
        for i in range(self._processes - len(self._pool)):
            w = self.Process(target=Worker(),
                             args=(self._inqueue, self._outqueue,
                                   self._initializer,
                                   self._initargs, self._maxtasksperchild)
                             )
            self._pool.append(w)
            w.name = w.name.replace('Process', 'PoolWorker')
            w.daemon = True
            w.start()
            debug('added worker')

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

    def inspect_threads(self):
        """
        This method inspects the attributes exposed by the Worker object defined
        above and lets us debug the thread pool.

        This is useful for answering the question: "What functions are running in
        the pool right now?"

        :return: Data as a list of dicts, which is usually sent to inspect_data_to_log()
        """
        inspect_data = []

        for process in self._pool[:]:
            worker_state = process.get_state()
            inspect_data.append(worker_state)

        return inspect_data
