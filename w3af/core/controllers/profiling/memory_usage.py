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
import os

from .utils import get_filename_fmt, dump_data_every_thread, cancel_thread


PROFILING_OUTPUT_FMT = '/tmp/w3af-%s-%s.memory'
DELAY_MINUTES = 2
SAVE_THREAD_PTR = []


def user_wants_memory_profiling():
    _should_profile = os.environ.get('W3AF_MEMORY_PROFILING', '0')

    if _should_profile.isdigit() and int(_should_profile) == 1:
        return True

    return False


def should_profile_memory(wrapped):
    def inner():
        if user_wants_memory_profiling():
            return wrapped()

    return inner


@should_profile_memory
def start_memory_profiling():
    """
    If the environment variable W3AF_PROFILING is set to 1, then we start
    the CPU and memory profiling.

    :return: None
    """
    dump_data_every_thread(dump_objects, DELAY_MINUTES, SAVE_THREAD_PTR)


def dump_objects():
    """
    This is a thread target which every X minutes
    """
    # pylint: disable=E0401
    from meliae import scanner
    scanner.dump_all_objects(PROFILING_OUTPUT_FMT % get_filename_fmt())
    # pylint: enable=E0401


@should_profile_memory
def stop_memory_profiling():
    """
    We cancel the save thread and dump objects for the last time.
    """
    cancel_thread(SAVE_THREAD_PTR)
    dump_objects()
