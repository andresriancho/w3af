"""This module exposes function  timelimited and two
   classes  TimeLimited and  TimeLimitExpired.

   Function  timelimited can be used to invoke any
   callable object with a time limit.

   Class  TimeLimited wraps any callable object into a
   time limited callable with an equivalent signature.

   Beware, any critical resources like locks, memory or
   files, etc. acquired or opened by the callable may
   not be released respectively closed.  Therefore,
   time limiting such callables may cause deadlock or
   leaks or both.

   No signals or timers are affected and any errors are
   propagated as usual.  Decorators and with statements
   are avoided for backward compatibility.

   Tested with Python 2.2.3, 2.3.7, 2.4.5, 2.5.2, 2.6.2
   or 3.0.1 on CentOS 4.7, MacOS X 10.4.11 Tiger (Intel)
   and 10.3.9 Panther (PPC), Solaris 10 and Windows XP.

   Note, for Python 3.0 and beyond, replace ', e:' with
   ' as e:' in the 3 except lines marked #XXX below or
   run the Python 2to3 translator on this file, see
   <http://docs.python.org/dev/3.1/library/2to3.html>

   The core of the function  timelimited is copied from
   <http://code.activestate.com/recipes/473878/>.
"""
__all__ = ('timelimited', 'TimeLimited', 'TimeLimitExpired')
__version__ = '4  2009-06-08'

import traceback

from multiprocessing.dummy import Process

# The #PYCHOK marks are intended for postprocessing
# by <http://code.activestate.com/recipes/546532/>

# UGLY! private method __stop
# pylint: disable=E1101
try:
    _Thread_stop = Process._Thread__stop  # PYCHOK false
except AttributeError:  # _stop in Python 3.0
    _Thread_stop = Process._stop  # PYCHOK expected


class TimeLimitExpired(Exception):
    """Exception raised when time limit expires.
    """
    pass


def timelimited(timeout, function, *args, **kwds):
    """Invoke the given function with the positional and
       keyword arguments under a time constraint.

       The function result is returned if the function
       finishes within the given time limit, otherwise
       a TimeLimitExpired error is raised.

       The timeout value is in seconds and has the same
       resolution as the standard time.time function.  A
       timeout value of None invokes the given function
       without imposing any time limit.

       A TypeError is raised if function is not callable,
       a ValueError is raised for negative timeout values
       and any errors occurring inside the function are
       passed along as-is.
    """
    class _Timelimited(Process):
        _error_ = TimeLimitExpired  # assume timeout
        _result_ = None

        def run(self):
            try:
                self._result_ = function(*args, **kwds)
            except Exception, e:  # XXX as for Python 3.0
                e.orig_traceback_str = traceback.format_exc()
                self._error_ = e
            else:
                self._error_ = None

        def _stop(self):
            # UGLY! force the thread to stop by (ab)using
            # the private __stop or _stop method, but that
            # seems to work better than these recipes
            # <http://code.activestate.com/recipes/496960/>
            # <http://sebulba.wikispaces.com/recipe+thread2>
            if self.isAlive():
                _Thread_stop(self)

    if not hasattr(function, '__call__'):
        raise TypeError('function not callable: %s' % repr(function))

    if timeout is None:  # shortcut
        return function(*args, **kwds)

    if timeout < 0:
        raise ValueError('timeout invalid: %s' % repr(timeout))

    t = _Timelimited()
    t.start()
    t.join(timeout)

    if t._error_ is None:
        return t._result_

    if t._error_ is TimeLimitExpired:
        t._stop()
        raise TimeLimitExpired('timeout %r for %s' % (timeout, repr(function)))
    else:
        raise t._error_


class TimeLimited(object):
    """Create a time limited version of any callable.

       For example, to limit function f to t seconds,
       first create a time limited version of f.

         from timelimited import *

         f_t = TimeLimited(f, t)

      Then, instead of invoking f(...), use f_t like

         try:
             r = f_t(...)
         except TimeLimitExpired:
             r = ...  # timed out

    """
    def __init__(self, function, timeout=None):
        """See function  timelimited for a description
           of the arguments.
        """
        self._function = function
        self._timeout = timeout

    def __call__(self, *args, **kwds):
        """See function  timelimited for a description
           of the behavior.
        """
        return timelimited(self._timeout, self._function, *args, **kwds)

    def __str__(self):
        return '<%s of %r, timeout=%s>' % (repr(self)[1:-1], self._function, self._timeout)

    def _timeout_get(self):
        return self._timeout

    def _timeout_set(self, timeout):
        self._timeout = timeout
    timeout = property(_timeout_get, _timeout_set, None,
                       'Property to get and set the timeout value')
