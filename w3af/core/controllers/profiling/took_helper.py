"""
took_helper.py

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
import time

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.profiling.thread_time import thread_active_time, CPU_TIME_IS_ACTIVE


class TimeStamp(object):
    def __init__(self):
        if CPU_TIME_IS_ACTIVE:
            self.thread_cpu_time = thread_active_time()
            self.wall_time = time.time()
        else:
            self.thread_cpu_time = None
            self.wall_time = time.time()


def get_start_timestamp():
    return TimeStamp()


def get_end_timestamp():
    return TimeStamp()


def write_took_debug(plugin_name, method_name, timestamp_a, timestamp_b, method_params=None):
    """
    Write the "took X seconds" line to the debug log

    :param plugin_name: The plugin name
    :param method_name: The method name of plugin which was invoked
    :param timestamp_a: Start timestamp
    :param timestamp_b: End timestamp
    :param method_params: Optional parameters sent to the plugin.method().
                          This should be a dict with parameter names as keys
                          and strings as values.
    :return: None, debug line written to log.
    """
    method_params = dict() if method_params is None else method_params
    params_str = ','.join('%s="%s"' % (key, value) for key, value in method_params.iteritems())

    if CPU_TIME_IS_ACTIVE:
        spent_wall_time = timestamp_b.wall_time - timestamp_a.wall_time
        spent_cpu_time = timestamp_b.thread_cpu_time - timestamp_a.thread_cpu_time

        args = (plugin_name,
                method_name,
                params_str,
                spent_wall_time,
                spent_cpu_time,
                spent_cpu_time / spent_wall_time * 100)

        #
        # Note to self: if the % of CPU time is high then the plugin is CPU-bound
        #               and can be improved by changing the algorithms used,
        #               this was the case for difflib.SequenceMatcher in blind SQL
        #               injection plugin
        #
        msg = '%s.%s(%s) took %.2f seconds to run (%.2f seconds / %i%% consuming CPU cycles)'
        om.out.debug(msg % args)

    else:
        spent_wall_time = timestamp_b.wall_time - timestamp_a.wall_time

        args = (plugin_name,
                method_name,
                url,
                did,
                spent_wall_time)

        #
        # Note to self: wall time is not a good performance indicator for plugins
        #               since they are run in threads and at any point the kernel
        #               can switch to a different thread and pause the current thread
        #               the wall time will keep running and the thread is not doing
        #               anything.
        #
        msg = '%s.%s(url="%s", did=%s) took %.2f seconds to run'
        om.out.debug(msg % args)

