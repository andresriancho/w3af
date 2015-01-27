"""
pytracemalloc.py

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
import sys
import gc
import cPickle


def user_wants_pytracemalloc():
    _should_profile = os.environ.get('W3AF_PYTRACEMALLOC', '0')

    if _should_profile.isdigit() and int(_should_profile) == 1:
        return True

    return False


if user_wants_pytracemalloc():
    try:
        # User's don't need this module, and installation is complex
        # http://pytracemalloc.readthedocs.org/install.html
        import tracemalloc
    except ImportError, ie:
        print('Failed to import tracemalloc: %s' % ie)
        sys.exit(-1)


from .utils import get_filename_fmt, dump_data_every_thread, cancel_thread


PROFILING_OUTPUT_FMT = '/tmp/w3af-%s-%s.tracemalloc'
DELAY_MINUTES = 2
SAVE_TRACEMALLOC_PTR = []


def should_dump_tracemalloc(wrapped):
    def inner():
        if user_wants_pytracemalloc():
            return wrapped()

    return inner


@should_dump_tracemalloc
def start_tracemalloc_dump():
    """
    If the environment variable W3AF_PYTRACEMALLOC is set to 1, then we start
    the thread that will dump the memory usage data which can be retrieved
    using tracemalloc module.

    :return: None
    """
    # save 25 frames
    tracemalloc.start(25)

    dump_data_every_thread(dump_tracemalloc, DELAY_MINUTES, SAVE_TRACEMALLOC_PTR)


def dump_tracemalloc():
    """
    Dumps memory usage information to file
    """
    gc.collect()
    snapshot = tracemalloc.take_snapshot()

    output_file = PROFILING_OUTPUT_FMT % get_filename_fmt()
    with open(output_file, 'wb') as fp:
        cPickle.dump(snapshot, fp, 2)

    # Make sure the snapshot goes away
    snapshot = None


@should_dump_tracemalloc
def stop_tracemalloc_dump():
    """
    Save profiling information (if available)
    """
    cancel_thread(SAVE_TRACEMALLOC_PTR)
    dump_tracemalloc()
