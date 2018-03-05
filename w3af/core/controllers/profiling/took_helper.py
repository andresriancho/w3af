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


class TookLine(object):
    def __init__(self, w3af_core, plugin_name, method_name, debugging_id=None, method_params=None):
        """
        Write the "took X seconds" line to the debug log

        :param w3af_core: The w3af core instance
        :param plugin_name: The plugin name
        :param method_name: The method name of plugin which was invoked
        :param debugging_id: The unique ID used for tracking requests
        :param method_params: Optional parameters sent to the plugin.method().
                              This should be a dict with parameter names as keys
                              and strings as values.
        """
        self._w3af_core = w3af_core
        self._plugin_name = plugin_name
        self._method_name = method_name
        self._method_params = method_params
        self._debugging_id = debugging_id
        self._start = None
        self._end = None

        self.start()
    
    def start(self):
        self._start = TimeStamp()
    
    def end(self):
        self._end = TimeStamp()
        
    def send(self):
        """
        Write the "took X seconds" line to the debug log
        :return: None, debug line written to log.
        """
        #
        # Note to self: wall time is not a good performance indicator for plugins
        #               since they are run in threads and at any point the kernel
        #               can switch to a different thread and pause the current thread
        #               the wall time will keep running and the thread is not doing
        #               anything.
        #
        self.end()
        parentheses_data = []
        spent_wall_time = self._end.wall_time - self._start.wall_time

        #
        #   Prepare the user provided data
        #
        method_params = dict() if self._method_params is None else self._method_params

        # If debugging_id was defined then we add it to the parameters
        if self._debugging_id:
            method_params['did'] = self._debugging_id

        params_str = ','.join('%s="%s"' % (key, value) for key, value in method_params.iteritems())

        #
        #   Query the extended urllib to check if it has RTT data regarding this debugging_id
        #
        rtt = self._w3af_core.uri_opener.get_rtt_for_debugging_id(self._debugging_id)

        if rtt is not None and rtt >= 0.01:
            #
            # Note to self: When you see something like "583% sending HTTP requests" it is not
            #               a bug, it simply indicates that many threads were used to send
            #               your HTTP requests and thus the sum(RTT) is higher than the wall
            #               time
            #
            msg = '%.2fs %i%% sending HTTP requests'
            msg %= (rtt, rtt / spent_wall_time * 100)
            parentheses_data.append(msg)

        #
        #   Only show the CPU time for this thread if the method to extract that data
        #   is available in this system AND if it is worth it: short execution times will
        #   never be investigated
        #
        if CPU_TIME_IS_ACTIVE and spent_wall_time >= 0.2:
            #
            # Note to self: if the % of CPU time is high then the plugin is CPU-bound
            #               and can be improved by changing the algorithms used,
            #               this was the case for difflib.SequenceMatcher in blind SQL
            #               injection plugin
            #
            spent_cpu_time = self._end.thread_cpu_time - self._start.thread_cpu_time

            if (spent_cpu_time / spent_wall_time) >= 0.2:
                msg = '%.2fs %i%% consuming CPU cycles'
                msg %= (spent_cpu_time, spent_cpu_time / spent_wall_time * 100)

                parentheses_data.append(msg)

        #
        # Now we write the line to the log
        #
        args = (self._plugin_name,
                self._method_name,
                params_str,
                spent_wall_time)

        msg = '%s.%s(%s) took %.2fs to run'
        msg %= args

        #
        # Adding any extras we might have
        #
        if parentheses_data:
            msg += ' (%s)' % ', '.join(parentheses_data)

        om.out.debug(msg)
