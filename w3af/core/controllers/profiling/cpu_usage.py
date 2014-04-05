"""
cpu_usage.py

Copyright 2012 Andres Riancho

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
from .utils import (should_profile, get_filename_fmt, dump_data_every_thread,
                    cancel_thread)


PROFILING_OUTPUT_FMT = '/tmp/w3af-%s-%s.cpu'
DELAY_MINUTES = 2
SAVE_THREAD_PTR = []


def start_cpu_profiling():
    """
    If the environment variable W3AF_PROFILING is set to 1, then we start
    the CPU and memory profiling.

    :return: None
    """
    if not should_profile():
        return

    import yappi
    yappi.start()

    dump_data_every_thread(dump_data, DELAY_MINUTES, SAVE_THREAD_PTR)


def dump_data():
    import yappi
    yappi.get_func_stats().save(PROFILING_OUTPUT_FMT % get_filename_fmt(),
                                type="pstat")


def stop_cpu_profiling():
    """
    Save profiling information (if available)
    """
    if not should_profile():
        return

    cancel_thread(SAVE_THREAD_PTR)
    dump_data()
