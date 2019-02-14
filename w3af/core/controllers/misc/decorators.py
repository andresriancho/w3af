"""
decorators.py

Copyright 2011 Andres Riancho

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
import math
import time
import threading
import functools

from functools import wraps

import w3af.core.controllers.output_manager as om

# pylint: disable=E0401
from darts.lib.utils.lru import SynchronizedLRUDict
# pylint: enable=E0401


def runonce(exc_class=Exception):
    """
    Function to decorate methods that should be called only once.

    :param exc_class: The Exception class to be raised when the method has
        already been called.
    """
    def runonce_meth(meth):
        
        @wraps(meth)
        def inner_runonce_meth(self, *args):
            if not getattr(self, '_already_executed', False):
                self._already_executed = True
                return meth(self, *args)
            raise exc_class()
        return inner_runonce_meth
    
    return runonce_meth


def retry(tries, delay=1, backoff=2, exc_class=None, err_msg='', log_msg=None):
    """
    Retries a function or method if an exception was raised.

    :param tries: Number of attempts. Must be >= 1.
    :param delay: Initial delay before retrying. Must be non negative.
    :param backoff: Indicates how much the delay should lengthen after
                    each failure. Must greater than 1.
    :param exc_class: Exception class to use if all attempts have been
                      exhausted.
    :param err_msg: Error message to use when an instance of `exc_class`
                    is raised. If no value is passed the string representation
                    of the current exception is used.
    """
    if backoff <= 1:
        raise ValueError("'backoff' must be greater than 1")

    tries = math.floor(tries)
    if tries < 1:
        raise ValueError("'tries' must be 1 or greater.")

    if delay < 0:
        raise ValueError("'delay' must be non negative.")

    def deco_retry(f):
        
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries - 1, delay

            while mtries >= 0:
                try:
                    rv = f(*args, **kwargs)
                except Exception, ex:
                    # Ok, fail!
                    if mtries == 0:
                        if exc_class:
                            raise exc_class(err_msg or str(ex))
                        raise
                else:
                    return rv

                mtries -= 1
                time.sleep(mdelay)
                mdelay *= backoff

                if log_msg is not None:
                    om.out.debug(log_msg)

        return f_retry
    
    return deco_retry


def cached_property(fun):
    """
    A memoize decorator for class properties.
    """
    @wraps(fun)
    def get(self):
        try:
            return self._cache[fun]
        except AttributeError:
            self._cache = {}
        except KeyError:
            pass
        ret = self._cache[fun] = fun(self)
        return ret

    return property(get)


class memoized(object):
    """
    Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    """
    def __init__(self, func, lru_size=10):
        self.func = func
        self.cache = SynchronizedLRUDict(lru_size)

    def __call__(self, *args, **kwargs):
        try:
            result = self.cache[(args, tuple(kwargs.items()))]
        except KeyError:
            value = self.func(*args, **kwargs)
            self.cache[(args, tuple(kwargs.items()))] = value
            return value
        else:
            return result

    def __repr__(self):
        """
        Return the function's docstring.
        """
        return self.func.__doc__

    def __get__(self, obj, objtype):
        """
        Support instance methods.
        """
        return functools.partial(self.__call__, obj)


def rate_limited(max_per_second):
    """
    Decorator that make functions not be called faster than
    """
    lock = threading.Lock()
    min_interval = 1.0 / float(max_per_second)

    def decorate(func):
        last_time_called = [0.0]

        @wraps(func)
        def rate_limited_function(*args, **kwargs):
            lock.acquire()
            elapsed = time.clock() - last_time_called[0]
            left_to_wait = min_interval - elapsed

            if left_to_wait > 0:
                time.sleep(left_to_wait)

            lock.release()

            ret = func(*args, **kwargs)
            last_time_called[0] = time.clock()
            return ret

        return rate_limited_function

    return decorate