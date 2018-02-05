"""
thread_state_observer.py

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
import threading
import time
import re

import w3af.core.controllers.output_manager as om

from w3af.core.data.misc.encoding import smart_str_ignore
from .strategy_observer import StrategyObserver


class ThreadStateObserver(StrategyObserver):
    """
    Monitor number jobs which are running in the different threads.
    """
    ANALYZE_EVERY = 30
    DISCOVER_WORKER_RE = re.compile('<bound method crawl_infrastructure._discover_worker'
                                    ' of <crawl_infrastructure\(CrawlInfraController,'
                                    ' started daemon .*?\)>>')

    def __init__(self):
        super(ThreadStateObserver, self).__init__()
        self.audit_thread = None
        self.crawl_infra_thread = None
        self.should_stop = False
        self._lock = threading.RLock()

    def end(self):
        self.should_stop = True

        if self.crawl_infra_thread is not None:
            self.crawl_infra_thread.join()

        if self.audit_thread is not None:
            self.audit_thread.join()

    def crawl(self, consumer, *args):
        """
        Log the thread state for crawl infra plugins

        :param consumer: A crawl consumer instance
        :param args: Fuzzable requests that we don't care about
        :return: None, everything is written to disk
        """
        with self._lock:
            if self.crawl_infra_thread is not None:
                return

            self.crawl_infra_thread = threading.Thread(target=self.thread_worker,
                                                       args=(consumer, 'CrawlInfraWorker'),
                                                       name='CrawlInfraPoolStateObserver')
            self.crawl_infra_thread.start()

    def audit(self, consumer, *args):
        """
        Log the thread state for audit plugins

        :param consumer: An audit consumer instance
        :param args: Fuzzable requests that we don't care about
        :return: None, everything is written to disk
        """
        with self._lock:
            if self.audit_thread is not None:
                return

            self.audit_thread = threading.Thread(target=self.thread_worker,
                                                 args=(consumer, 'AuditorWorker'),
                                                 name='AuditPoolStateObserver')
            self.audit_thread.start()

    def thread_worker(self, consumer, name):
        last_call = 0

        while not self.should_stop:
            #
            # The logic below makes sure that on average we wait 1 second (2/2)
            # for the thread to join() when end() is called, and also that we
            # print the stats to the log every ~30 seconds.
            #
            time.sleep(2)

            current_time = time.time()
            if (current_time - last_call) < self.ANALYZE_EVERY:
                continue

            last_call = current_time

            #
            # Now the real deal
            #
            pool = consumer.get_pool()

            if pool is None:
                self.write_to_log('The %s consumer finished all tasks and closed the pool.' % name)
                self.write_to_log('100%% of %s workers are idle.' % name)
                break

            inspect_data = pool.inspect_threads()
            self.inspect_data_to_log(pool, inspect_data)

    def inspect_data_to_log(self, pool, inspect_data):
        """
        Print the inspect_threads data to the log files

        def get_state(self):
            return {'func_name': self.func_name,
                    'args': self.args,
                    'kwargs': self.kwargs,
                    'start_time': self.start_time,
                    'idle': self.is_idle(),
                    'job': self.job,
                    'worker_id': self.id}

        :return: None
        """
        name = pool.worker_names

        if not len(inspect_data):
            self.write_to_log('No pool workers at %s.' % (name,))
            return

        #
        #   Write the detailed information
        #
        for worker_state in inspect_data:
            if worker_state['idle']:
                message = 'Worker with ID %s(%s) is idle.'
                message %= (worker_state['name'],
                            worker_state['worker_id'])

            else:
                spent = time.time() - worker_state['start_time']
                args_str = ', '.join(smart_str_ignore(repr(arg)) for arg in worker_state['args'])
                kwargs_str = smart_str_ignore(worker_state['kwargs'])

                func_name = smart_str_ignore(worker_state['func_name'])
                func_name = self.clean_function_name(func_name)

                message = ('Worker with ID %s(%s) has been running job %s for %.2f seconds.'
                           ' The job is: %s(%s, kwargs=%s)')
                message %= (worker_state['name'],
                            worker_state['worker_id'],
                            worker_state['job'],
                            spent,
                            func_name,
                            args_str,
                            kwargs_str)

            self.write_to_log(message)

        #
        #   Write some stats
        #
        total_workers = len(inspect_data)
        idle_workers = 0.0

        for worker_state in inspect_data:
            if worker_state['idle']:
                idle_workers += 1

        idle_perc = (idle_workers / total_workers) * 100
        self.write_to_log('%i%% of %s workers are idle.' % (idle_perc, name))

    def write_to_log(self, message):
        om.out.debug(message)

    def clean_function_name(self, function_name):
        if self.DISCOVER_WORKER_RE.search(function_name):
            return '_discover_worker'

        return function_name
