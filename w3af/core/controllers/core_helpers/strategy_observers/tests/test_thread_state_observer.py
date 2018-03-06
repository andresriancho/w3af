"""
test_thread_state_observer.py

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
import unittest
import time

from w3af.core.controllers.threads.threadpool import Pool
from w3af.core.controllers.core_helpers.strategy_observers.thread_state_observer import ThreadStateObserver


class TestThreadStateObserver(unittest.TestCase):
    def test_inspect_data_to_log(self):
        worker_pool = Pool(processes=1, worker_names='WorkerThread')
        tso = ThreadStateObserver()

        messages = []

        def save_messages(message):
            messages.append(message)

        tso.write_to_log = save_messages

        def sleep(sleep_time, **kwargs):
            time.sleep(sleep_time)

        args = (2,)
        kwds = {'x': 2}
        worker_pool.apply_async(func=sleep, args=args, kwds=kwds)

        # Let the worker get the task
        time.sleep(0.3)

        worker_states = worker_pool.inspect_threads()
        tso.inspect_data_to_log(worker_pool, worker_states)

        self.assertEqual(len(messages), 2, messages)

        message_re = ('Worker with ID .*? has been running job .*? for .*? seconds.'
                      ' The job is: .*?(.*?, kwargs=.*?)')
        self.assertRegexpMatches(messages[0], message_re)
        self.assertEqual(messages[1], '0% of WorkerThread workers are idle.')
