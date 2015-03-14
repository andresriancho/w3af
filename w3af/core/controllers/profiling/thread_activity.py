"""
thread_activity.py

Copyright 2014 Andres Riancho

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
import json
import threading
import traceback

from .utils import get_filename_fmt, dump_data_every_thread, cancel_thread


PROFILING_OUTPUT_FMT = '/tmp/w3af-%s-%s.threads'
DELAY_MINUTES = 2
SAVE_THREAD_PTR = []


def should_dump_thread_stack(wrapped):
    def inner():
        _should_profile = os.environ.get('W3AF_THREAD_ACTIVITY', '0')

        if _should_profile.isdigit() and int(_should_profile) == 1:
            return wrapped()

    return inner


@should_dump_thread_stack
def start_thread_stack_dump():
    """
    If the environment variable W3AF_THREAD_ACTIVITY is set to 1, then we start
    the thread that will dump the current line being executed of every thread
    in the w3af process to a file.

    :return: None
    """
    dump_data_every_thread(dump_thread_stack, DELAY_MINUTES, SAVE_THREAD_PTR)


def get_thread_name(threads_list, thread_id):
    """
    :param threads_list: The list of all active threads in the system
    :param thread_id: The ident of the thread we want the name for
    :return: A thread name or None
    """
    for thread in threads_list:
        if thread.ident == thread_id:
            return thread.name

    return None


def dump_thread_stack():
    """
    Dumps all thread stacks to a file
    """
    threads = threading.enumerate()
    output_file = PROFILING_OUTPUT_FMT % get_filename_fmt()
    data = {}

    for thread, frame in sys._current_frames().items():
        # Actually saving it as a list makes it more human readable
        trace = traceback.format_stack(frame)

        data['%x' % thread] = {'traceback': trace,
                               'name': get_thread_name(threads, thread)}

    json.dump(data, file(output_file, 'w'), indent=4)


@should_dump_thread_stack
def stop_thread_stack_dump():
    """
    Save profiling information (if available)
    """
    cancel_thread(SAVE_THREAD_PTR)
    dump_thread_stack()

