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
    > The amount of time the CPU spent on the given thread.

The thread could be in three states:
   #1 Waiting for IO (network, fs, etc)
   #2 IDLE (kernel paused the thread)
   #3 Running thread code (consuming CPU cycles)
   #4 Running kernel code associated with the thread (consuming CPU cycles)

thread_active_time() returns (#3 + #4) 

The problem I'm trying to solve is explained by me in an email to the 
PyAR mailing list [0], and the inspiration for this implementation comes 
from the monotonic [1] module.

Please note that this method *only works on linux*, for any other operating
systems I just return the result of calling time.time().

[0] http://listas.python.org.ar/pipermail/pyar/2018-January/042412.html
[1] https://github.com/atdt/monotonic/blob/master/monotonic.py
"""

__all__ = ('thread_active_time',
           'CPU_TIME_IS_ACTIVE')


CPU_TIME_IS_ACTIVE = False


if not sys.platform.startswith('linux'):
    #
    # Fallback to time.time
    #
    thread_active_time = time.time

else:
    #
    # Only works in Linux
    #
    try:
        try:
            getrusage = ctypes.CDLL(ctypes.util.find_library('c'),
                                    use_errno=True).getrusage
        except Exception:
            getrusage = ctypes.CDLL(ctypes.util.find_library('rt'),
                                    use_errno=True).getrusage
    except:
        #
        # Something went wrong, either ctypes is not finding the libraries, or
        # they are not there. Fallback to time.time
        #
        thread_active_time = time.time
    else:
        class timeval(ctypes.Structure):
            _fields_ = [("tv_sec", ctypes.c_long), ("tv_usec", ctypes.c_long)]

        class rusage_struct(ctypes.Structure):
            """
            The structure where the result is written to, as described in:

            https://github.com/torvalds/linux/blob/master/include/uapi/linux/resource.h#L24
            http://man7.org/linux/man-pages/man2/getrusage.2.html
            """
            _fields_ = (('ru_utime', timeval),
                        ('ru_stime', timeval),
                        ('ru_maxrss', ctypes.c_long),
                        ('ru_ixrss', ctypes.c_long),
                        ('ru_idrss', ctypes.c_long),
                        ('ru_isrss', ctypes.c_long),
                        ('ru_minflt', ctypes.c_long),
                        ('ru_majflt', ctypes.c_long),
                        ('ru_nswap', ctypes.c_long),
                        ('ru_inblock', ctypes.c_long),
                        ('ru_oublock', ctypes.c_long),
                        ('ru_msgsnd', ctypes.c_long),
                        ('ru_msgrcv', ctypes.c_long),
                        ('ru_nsignals', ctypes.c_long),
                        ('ru_nvcsw', ctypes.c_long),
                        ('ru_nivcsw', ctypes.c_long),
            )

        # https://github.com/torvalds/linux/blob/master/include/uapi/linux/resource.h#L22
        RUSAGE_THREAD = 1
        CPU_TIME_IS_ACTIVE = True

        def thread_active_time():
            """
            :return: The time this thread has been running:

                        user time [0] + system time [1]

            Usually it is possible to know how much IDLE time a thread has had in a period
            of time by subtracting the wall time from the result of this function.

            [0] https://github.com/torvalds/linux/blob/master/include/uapi/linux/resource.h#L25
            [1] https://github.com/torvalds/linux/blob/master/include/uapi/linux/resource.h#L26
            """
            ru = rusage_struct()
            if getrusage(RUSAGE_THREAD, ctypes.pointer(ru)):
                errno = ctypes.get_errno()
                raise OSError(errno, os.strerror(errno))

            user = ru.ru_utime.tv_sec + ru.ru_utime.tv_usec / 1.0e6
            system = ru.ru_stime.tv_sec + ru.ru_stime.tv_usec / 1.0e6

            return user + system
