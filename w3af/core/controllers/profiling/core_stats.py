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
import traceback
import json
import sys
import os

from functools import partial

import w3af.core.controllers.output_manager as om
from w3af.core.controllers.misc.number_generator import consecutive_number_generator
from .utils import get_filename_fmt, dump_data_every_thread, cancel_thread


PROFILING_OUTPUT_FMT = '/tmp/w3af-%s-%s.core'
DELAY_MINUTES = 2
SAVE_THREAD_PTR = []


def core_profiling_is_enabled():
    env_value = os.environ.get('W3AF_CORE_PROFILING', '0')

    if env_value.isdigit() and int(env_value) == 1:
        return True

    return False


def should_profile_core(wrapped):
    def inner(w3af_core):
        if core_profiling_is_enabled():
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

                'Crawl input queue input speed': s.get_crawl_input_speed(),
                'Crawl input queue output speed': s.get_crawl_output_speed(),
                'Crawl input queue size': s.get_crawl_qsize(),
                'Crawl output queue size': s.get_crawl_output_qsize(),

                'Audit input queue input speed': s.get_audit_input_speed(),
                'Audit input queue output speed': s.get_audit_output_speed(),
                'Audit input queue size': s.get_audit_qsize(),

                'Grep input queue size': s.get_audit_qsize(),

                'Core worker pool input queue size': s.get_core_worker_pool_queue_size(),

                'Output manager input queue size': om.manager.get_in_queue().qsize(),

                'Cache stats': get_parser_cache_stats()}
    except Exception, e:
        exc_type, exc_value, exc_tb = sys.exc_info()
        tback = traceback.format_exception(exc_type, exc_value, exc_tb)

        data = {'Exception': str(e),
                'Traceback': tback}

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


def get_parser_cache_stats():
    import w3af.core.data.parsers.parser_cache as parser_cache
    from w3af.core.data.parsers.mp_document_parser import mp_doc_parser
    
    r = {'hit_rate': parser_cache.dpc.get_hit_rate(),
         'max_lru_items': parser_cache.dpc.get_max_lru_items(),
         'current_lru_size': parser_cache.dpc.get_current_lru_items(),
         'total_cache_queries': parser_cache.dpc.get_total_queries(),
         'do_not_cache': parser_cache.dpc.get_do_not_cache()}

    if mp_doc_parser._pool is not None:
        r['Parser pool worker size'] = mp_doc_parser._pool._context.workers
        r['Parser pool input queue size'] = mp_doc_parser._pool._context.task_queue.qsize()
    else:
        r['Parser pool worker size'] = 0
        r['Parser pool input queue size'] = 0

    return r
