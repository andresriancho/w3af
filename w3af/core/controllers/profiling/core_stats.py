"""
core_stats.py

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
import json
import os

from functools import partial

from w3af.core.controllers.misc.number_generator import consecutive_number_generator
from .utils import get_filename_fmt, dump_data_every_thread, cancel_thread


PROFILING_OUTPUT_FMT = '/tmp/w3af-%s-%s.core'
DELAY_MINUTES = 2
SAVE_THREAD_PTR = []


def should_profile_core(wrapped):
    def inner(w3af_core):
        _should_profile = os.environ.get('W3AF_CORE_PROFILING', '0')

        if _should_profile.isdigit() and int(_should_profile) == 1:
            return wrapped(w3af_core)

    return inner


@should_profile_core
def start_core_profiling(w3af_core):
    """
    If the environment variable W3AF_PROFILING is set to 1, then we start
    the CPU and memory profiling.

    :return: None
    """
    dd_partial = partial(dump_data, w3af_core)
    dump_data_every_thread(dd_partial, DELAY_MINUTES, SAVE_THREAD_PTR)


def dump_data(w3af_core):
    s = w3af_core.status
    try:
        data = {'Requests sent': consecutive_number_generator.get(),
                'Requests per minute': s.get_rpm(),
                'Crawl queue input speed': s.get_crawl_input_speed(),
                'Crawl queue output speed': s.get_crawl_output_speed(),
                'Crawl queue size': s.get_crawl_qsize(),
                'Audit queue input speed': s.get_audit_input_speed(),
                'Audit queue output speed': s.get_audit_output_speed(),
                'Audit queue size': s.get_audit_qsize()}
    except Exception, e:
        print('Failed to retrieve status data: "%s"' % e)
    else:
        json_data = json.dumps(data, indent=4)
        output_file = PROFILING_OUTPUT_FMT % get_filename_fmt()
        file(output_file, 'w').write(json_data)


@should_profile_core
def stop_core_profiling(w3af_core):
    """
    Save profiling information (if available)
    """
    cancel_thread(SAVE_THREAD_PTR)
    dump_data(w3af_core)

