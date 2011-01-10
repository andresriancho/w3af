'''This module exposes function  timelimited and two
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
'''
__all__ = ('timelimited', 'TimeLimited', 'TimeLimitExpired')
__version__ = '4  2009-06-08'

from threading import Thread

# The #PYCHOK marks are intended for postprocessing
# by <http://code.activestate.com/recipes/546532/>

try:  # UGLY! private method __stop
    _Thread_stop = Thread._Thread__stop  #PYCHOK false
except AttributeError:  # _stop in Python 3.0
    _Thread_stop = Thread._stop  #PYCHOK expected


class TimeLimitExpired(Exception):
    '''Exception raised when time limit expires.
    '''
    pass


def timelimited(timeout, function, *args, **kwds):
    '''Invoke the given function with the positional and
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
    '''
    class _Timelimited(Thread):
        _error_  = TimeLimitExpired  # assume timeout
        _result_ = None

        def run(self):
            try:
                self._result_ = function(*args, **kwds)
                self._error_ = None
            except Exception, e:  #XXX as for Python 3.0
                import traceback
                e.orig_traceback_str = traceback.format_exc()
                self._error_ = e

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
    '''Create a time limited version of any callable.

       For example, to limit function f to t seconds,
       first create a time limited version of f.

         from timelimited import *

         f_t = TimeLimited(f, t)

      Then, instead of invoking f(...), use f_t like

         try:
             r = f_t(...)
         except TimeLimitExpired:
             r = ...  # timed out

    '''
    def __init__(self, function, timeout=None):
        '''See function  timelimited for a description
           of the arguments.
        '''
        self._function = function
        self._timeout  = timeout

    def __call__(self, *args, **kwds):
        '''See function  timelimited for a description
           of the behavior.
        '''
        return timelimited(self._timeout, self._function, *args, **kwds)

    def __str__(self):
        return '<%s of %r, timeout=%s>' % (repr(self)[1:-1], self._function, self._timeout)

    def _timeout_get(self):
        return self._timeout
    def _timeout_set(self, timeout):
        self._timeout = timeout
    timeout = property(_timeout_get, _timeout_set, None,
                       'Property to get and set the timeout value')


if __name__ == '__main__':

    import sys, time, threading  #PYCHOK expected

    _format = '%s test %%d/8 %%s in Python %s: %%s' % (
               sys.argv[0], sys.version.split()[0])
    _tests = 0

    def passed(arg='OK'):
        global _tests
        _tests += 1
        print(_format % (_tests, 'passed', arg))

    def failed(fmt, *args):
        global _tests
        _tests += 1
        if args:
            t = fmt % args
        else:
            t = fmt
        print(_format % (_tests, 'failed', t))

    def check(timeout, sleep, result, arg='OK'):
        if timeout > sleep:
            x = None  # time.sleep(0) result
        elif isinstance(result, TimeLimitExpired):
            x = result
        else:
            x = TimeLimitExpired
        if result is x:
            passed(arg)
        else:
            failed('expected %r, but got %r', x, result)


     # check timelimited function
    for t, s in ((2.0, 1),
                 (1.0, 20)):  # note, 20!
        try:
            r = timelimited(t, time.sleep, s)
        except Exception, e:  #XXX as for Python 3.0
            r = e
        check(t, s, r, timelimited)

     # check TimeLimited class and property
    f = TimeLimited(time.sleep)
    for t, s in ((2.0, 1),
                 (1.0, 20)):  # note, 20!
        f.timeout = t
        try:
            r = f(s)
        except Exception, e:  #XXX as for Python 3.0
            r = e
        check(t, s, r, f)

     # check TypeError
    try:
        t = timelimited(0, None)
        failed('no %r', TypeError)
    except TypeError:
        passed(TypeError)
    except:
        failed('expected %r', TypeError)

     # check ValueError
    try:
        t = timelimited(-10, time.time)
        failed('no %r', ValueError)
    except ValueError:
        passed(ValueError)
    except:
        failed('expected %r', ValueError)

     # check error passing from thread
    try:
        r = timelimited(1, lambda x: 1/x, 0)
        failed('no %r', ZeroDivisionError)
    except ZeroDivisionError:
        passed(ZeroDivisionError)
    except:
        failed('expected %r', ZeroDivisionError)

     # check that all created threads stopped
    for t in threading.enumerate():
        if t.isAlive() and repr(t).startswith('<_Timelimited('):
           failed('thread %r still alive', t)
           break
    else:
        passed('all _Timelimited threads stopped')
