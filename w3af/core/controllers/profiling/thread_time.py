"""
thread_time.py

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
import os
import sys
import time
import ctypes
import ctypes.util

"""
This file is a very hackish way to retrieve thread CPU time in Linux.

Definition of thread CPU time:
    > The amount of time the CPU spent on the given Thread.

The thread could be in three states:
 * Waiting for IO (network, fs, etc)
 * IDLE (kernel paused the thread)
 * Running (consuming CPU time) <-------- we measure this one with thread_cpu_time()

The problem I'm trying to solve is explained by me in an email to the 
PyAR mailing list [0], and the inspiration for this file comes from the 
monotonic [1] module.

Please note that this method *only works on linux*, for any other operating
systems I just return the result of calling time.time().

[0] http://listas.python.org.ar/pipermail/pyar/2018-January/042412.html
[1] https://github.com/atdt/monotonic/blob/master/monotonic.py
"""

__all__ = ('thread_cpu_time',)


if not sys.platform.startswith('linux'):
    #
    # Fallback to time.time
    #
    thread_cpu_time = time.time

else:
    #
    # Only works in Linux
    #
    try:
        try:
            clock_gettime = ctypes.CDLL(ctypes.util.find_library('c'),
                                        use_errno=True).clock_gettime
        except Exception:
            clock_gettime = ctypes.CDLL(ctypes.util.find_library('rt'),
                                        use_errno=True).clock_gettime
    except:
        #
        # Something went wrong, either ctypes is not finding the libraries, or
        # they are not there. Fallback to time.time
        #
        thread_cpu_time = time.time
    else:
        class timespec(ctypes.Structure):
            """Time specification, as described in clock_gettime(3)."""
            _fields_ = (('tv_sec', ctypes.c_long),
                        ('tv_nsec', ctypes.c_long))

        # https://code.woboq.org/userspace/glibc/sysdeps/unix/sysv/linux/bits/time.h.html#_M/CLOCK_THREAD_CPUTIME_ID
        CLOCK_THREAD_CPUTIME_ID = 3

        def thread_cpu_time():
            """Monotonic clock, cannot go backward."""
            ts = timespec()
            if clock_gettime(CLOCK_THREAD_CPUTIME_ID, ctypes.pointer(ts)):
                errno = ctypes.get_errno()
                raise OSError(errno, os.strerror(errno))
            print('xyz %s' % (ts.tv_sec + ts.tv_nsec / 1.0e9,))
            return ts.tv_sec + ts.tv_nsec / 1.0e9
