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
import Queue

from functools import partial

from multiprocessing.pool import ThreadPool
from multiprocessing.pool import RUN
from multiprocessing.dummy import Process

__all__ = ['Pool']


class one_to_many(object):
    """
    This is a simple wrapper that translates one argument to many in a function
    call. Useful for passing to the threadpool map function.
    """
    def __init__(self, func):
        self.func = func

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


class Pool(ThreadPool):

    def __init__(self, processes=None, initializer=None, initargs=(), worker_names=None):
        self.Process = partial(DaemonProcess, name=worker_names)
        ThreadPool.__init__(self, processes, initializer, initargs)
    
    def _setup_queues(self):
        self._inqueue = Queue.Queue()
        self._outqueue = Queue.Queue()
        self._quick_put = self._inqueue.put
        self._quick_get = self._outqueue.get
        
    def map_multi_args(self, func, iterable, chunksize=None):
        """
        Block until all results are done (please note the .get())
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
