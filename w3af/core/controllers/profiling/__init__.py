"""
__init__.py

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
from .cpu_usage import start_cpu_profiling, stop_cpu_profiling
from .memory_usage import start_memory_profiling, stop_memory_profiling
from .core_stats import start_core_profiling, stop_core_profiling
from .thread_activity import start_thread_stack_dump, stop_thread_stack_dump
from .processes import start_process_dump, stop_process_dump
from .psutil_stats import start_psutil_dump, stop_psutil_dump
from .pytracemalloc import start_tracemalloc_dump, stop_tracemalloc_dump


def start_profiling(w3af_core):
    start_cpu_profiling(w3af_core)
    start_memory_profiling(w3af_core)
    start_core_profiling(w3af_core)
    start_thread_stack_dump(w3af_core)
    start_process_dump(w3af_core)
    start_psutil_dump(w3af_core)
    start_tracemalloc_dump(w3af_core)


def stop_profiling(w3af_core):
    stop_cpu_profiling(w3af_core)
    stop_memory_profiling(w3af_core)
    stop_core_profiling(w3af_core)
    stop_thread_stack_dump(w3af_core)
    stop_process_dump(w3af_core)
    stop_psutil_dump(w3af_core)
    stop_tracemalloc_dump(w3af_core)