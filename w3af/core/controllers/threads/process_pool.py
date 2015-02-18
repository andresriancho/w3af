import os
import threading

from multiprocessing.pool import Pool, RUN, cpu_count, Finalize
from multiprocessing.process import Process, _cleanup, current_process

from w3af.core.controllers.threads.silent_joinable_queue import SilentJoinableQueue


class SubDaemonProcess(Process):
    """
    Get rid of "daemonic processes are not allowed to have children" message
    using the hack explained in:
    
    https://github.com/celery/celery/issues/1709
    https://github.com/celery/billiard/commit/e6bb0f744e97bd9acc560788a1b6152bc9ba48c3
    """
    _Popen = None

    def start(self):
        """
        Start child process
        """
        assert self._popen is None, 'cannot start a process twice'
        assert self._parent_pid == os.getpid(), \
               'can only start a process object created by current process'

        # This is the code I'm commenting out and allows me to perform the
        # dangerous task of forking inside a daemon process.
        """
        assert not current_process()._daemonic, \
               'daemonic processes are not allowed to have children'
        """

        _cleanup()
        if self._Popen is not None:
            Popen = self._Popen
        else:
            from multiprocessing.forking import Popen
        self._popen = Popen(self)
        current_process()._children.add(self)


class ProcessPool(Pool):
    """
    Extending the multiprocessing.Pool in order to:
        * Use SilentJoinableQueue as taskqueue
        * ...
    """
    Process = SubDaemonProcess

    def __init__(self, processes=None, initializer=None, initargs=(),
                 maxtasksperchild=None):
        self._setup_queues()
        self._taskqueue = SilentJoinableQueue()
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
            name='PoolWorkerHandler'
            )
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
