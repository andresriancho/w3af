"""
memory_usage.py

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
import threading
import time

from .utils import should_profile


PROFILING_OUTPUT_FMT = '/tmp/meliae-w3af-%s.memory'
DELAY_MINUTES = 2
SAVE_THREAD = None


def start_memory_profiling():
    """
    If the environment variable W3AF_PROFILING is set to 1, then we start
    the CPU and memory profiling.

    :return: None
    """
    if should_profile():
        dump_objects()


def dump_objects(start_thread=True):
    """
    This is a thread target which every X minutes
    """
    from meliae import scanner
    scanner.dump_all_objects(PROFILING_OUTPUT_FMT % time.time())

    if start_thread:
        global SAVE_THREAD
        SAVE_THREAD = threading.Timer(DELAY_MINUTES * 60, dump_objects)
        SAVE_THREAD.start()


def stop_memory_profiling():
    """
    We cancel the save thread and dump objects for the last time.
    """
    if SAVE_THREAD is not None:
        SAVE_THREAD.cancel()

    dump_objects(start_thread=False)