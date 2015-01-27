"""
processes.py

Copyright 2015 Andres Riancho

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
import json
import multiprocessing

from .utils import get_filename_fmt, dump_data_every_thread, cancel_thread


PROFILING_OUTPUT_FMT = '/tmp/w3af-%s-%s.processes'
DELAY_MINUTES = 2
SAVE_PROCESS_PTR = []


def should_dump_processes(wrapped):
    def inner():
        _should_profile = os.environ.get('W3AF_PROCESSES', '0')

        if _should_profile.isdigit() and int(_should_profile) == 1:
            return wrapped()

    return inner


@should_dump_processes
def start_process_dump():
    """
    If the environment variable W3AF_PROCESSES is set to 1, then we start
    the thread that will dump the sub processes created by this main thread.

    :return: None
    """
    dump_data_every_thread(dump_processes, DELAY_MINUTES, SAVE_PROCESS_PTR)


def dump_processes():
    """
    Dumps sub-process information to a file
    """
    output_file = PROFILING_OUTPUT_FMT % get_filename_fmt()
    data = {}

    for child in multiprocessing.active_children():
        pid = child._popen.pid
        child_data = {'name': child.name,
                      'daemon': child.daemon,
                      'exitcode': child.exitcode,
                      'target': child._target.__name__,
                      'args': [],
                      'kwargs': {}}

        for arg in child._args:
            try:
                json.dumps(arg)
            except (TypeError, UnicodeDecodeError):
                try:
                    child_data['args'].append(arg.__class__.__name__)
                except:
                    child_data['args'].append('undefined')
            else:
                child_data['args'].append(arg)

        for key, value in child._kwargs.iteritems():
            try:
                json.dumps(value)
            except (TypeError, UnicodeDecodeError):
                try:
                    child_data['kwargs'][key] = value.__class__.__name__
                except:
                    child_data['kwargs'][key] = 'undefined'
            else:
                child_data['kwargs'][key] = value

        data[pid] = child_data

    json.dump(data, file(output_file, 'w'), indent=4)


@should_dump_processes
def stop_process_dump():
    """
    Save profiling information (if available)
    """
    cancel_thread(SAVE_PROCESS_PTR)
    dump_processes()

