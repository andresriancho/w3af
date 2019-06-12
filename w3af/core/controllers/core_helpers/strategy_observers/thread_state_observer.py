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
import re
import sys
import time
import threading
import traceback

import w3af.core.controllers.output_manager as om

from w3af.core.data.misc.encoding import smart_str_ignore
from .strategy_observer import StrategyObserver


class ThreadStateObserver(StrategyObserver):
    """
    Monitor number jobs which are running in the different threads.
    """
    ANALYZE_EVERY = 30
    STACK_TRACE_MIN_TIME = 120
    DISCOVER_WORKER_RE = re.compile('<bound method CrawlInfrastructure._discover_worker'
                                    ' of <CrawlInfrastructure\(CrawlInfraController,'
                                    ' started daemon .*?\)>>')

    def __init__(self):
        super(ThreadStateObserver, self).__init__()

        self.should_stop = False

        self.audit_thread = None
        self.grep_thread = None
        self.crawl_infra_thread = None
        self.worker_thread = None

        self._audit_lock = threading.RLock()
        self._grep_lock = threading.RLock()
        self._crawl_infra_lock = threading.RLock()
        self._worker_thread_lock = threading.RLock()

    def end(self):
        self.should_stop = True

        if self.crawl_infra_thread is not None:
            self.crawl_infra_thread.join()

        if self.audit_thread is not None:
            self.audit_thread.join()

        if self.grep_thread is not None:
            self.grep_thread.join()

        if self.worker_thread is not None:
            self.worker_thread.join()

    def crawl(self, consumer, *args):
        """
        Log the thread state for crawl infra plugins

        :param consumer: A crawl consumer instance
        :param args: Fuzzable requests that we don't care about
        :return: None, everything is written to disk
        """
        if self.crawl_infra_thread is not None and self.worker_thread is not None:
            return

        with self._crawl_infra_lock:
            if self.crawl_infra_thread is None:

                pool = consumer.get_pool()
                self.crawl_infra_thread = threading.Thread(target=self.thread_worker,
                                                           args=(pool, 'CrawlInfraWorker'),
                                                           name='CrawlInfraPoolStateObserver')
                self.crawl_infra_thread.start()

        with self._worker_thread_lock:
            if self.worker_thread is None:
                pool = consumer._w3af_core.worker_pool
                self.worker_thread = threading.Thread(target=self.thread_worker,
                                                      args=(pool, 'Worker'),
                                                      name='WorkerPoolStateObserver')
                self.worker_thread.start()

    def audit(self, consumer, *args):
        """
        Log the thread state for audit plugins

        :param consumer: An audit consumer instance
        :param args: Fuzzable requests that we don't care about
        :return: None, everything is written to disk
        """
        if self.audit_thread is not None:
            return

        with self._audit_lock:
            if self.audit_thread is not None:
                return

            pool = consumer.get_pool()
            self.audit_thread = threading.Thread(target=self.thread_worker,
                                                 args=(pool, 'AuditorWorker'),
                                                 name='AuditPoolStateObserver')
            self.audit_thread.start()

    def grep(self, consumer, *args):
        """
        Log the thread state for grep plugins

        :param consumer: A grep consumer instance
        :param args: Fuzzable requests that we don't care about
        :return: None, everything is written to disk
        """
        if self.grep_thread is not None:
            return

        with self._grep_lock:
            if self.grep_thread is not None:
                return

            pool = consumer.get_pool()
            self.grep_thread = threading.Thread(target=self.thread_worker,
                                                args=(pool, 'GrepWorker'),
                                                name='GrepPoolStateObserver')
            self.grep_thread.start()

    def thread_worker(self, pool, name):
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
            if pool is None:
                self.write_to_log('The %s consumer finished all tasks and closed the pool.' % name)
                self.write_to_log('100%% of %s workers are idle.' % name)
                break

            inspect_data = pool.inspect_threads()
            inspect_data = self.add_thread_stack(inspect_data)
            self.inspect_data_to_log(pool, inspect_data)

            internal_thread_data = pool.get_internal_thread_state()
            self.internal_thread_data_to_log(pool, name, internal_thread_data)

            pool_queue_sizes = pool.get_pool_queue_sizes()
            self.pool_queue_sizes_to_log(pool, name, pool_queue_sizes)

    def add_thread_stack(self, inspect_data):
        """
        When threads have been running for a long time, it is not enough to
        log the initial function that the worker was told to run, we want to
        know exactly what function the thread is running *now*, including the
        whole traceback.
        """
        #
        #   Define which workers we want to inspect
        #
        workers_to_inspect = []

        for worker_state in inspect_data:
            if worker_state['idle'] or worker_state['start_time'] is None:
                continue

            spent = time.time() - worker_state['start_time']
            if spent < self.STACK_TRACE_MIN_TIME:
                continue

            workers_to_inspect.append(worker_state['worker_id'])

        #
        #   If there is nothing to do, just return to reduce the performance
        #   impact of this function
        #
        if not workers_to_inspect:
            return inspect_data

        #
        #   Find the workers in the thread list
        #
        for thread_id, frame in sys._current_frames().items():
            thread = self.get_thread_from_thread_id(thread_id)

            if thread is None:
                continue

            if not hasattr(thread, 'get_state'):
                continue

            state = thread.get_state()
            worker_id = state['worker_id']

            if worker_id not in workers_to_inspect:
                continue

            trace = []
            for filename, lineno, name, line in traceback.extract_stack(frame):
                trace.append('%s:%s @ %s()' % (filename, lineno, name))

            trace = trace[-10:]
            trace = ', '.join(trace)

            # Now save the trace to the inspect_data
            for worker_state in inspect_data:
                if worker_state['worker_id'] == worker_id:
                    worker_state['trace'] = trace

        return inspect_data

    def get_thread_from_thread_id(self, thread_id):
        for thread in threading.enumerate():
            if thread.ident == thread_id:
                return thread

    def pool_queue_sizes_to_log(self, pool, name, pool_queue_sizes):
        inqueue_size = pool_queue_sizes.get('inqueue_size', None)
        outqueue_size = pool_queue_sizes.get('outqueue_size', None)

        msg = '%s worker pool has %s tasks in inqueue and %s tasks in outqueue'
        args = (name,
                inqueue_size,
                outqueue_size)

        self.write_to_log(msg % args)

    def internal_thread_data_to_log(self, pool, name, internal_thread_data):
        worker_handler = internal_thread_data['worker_handler']
        task_handler = internal_thread_data['task_handler']
        result_handler = internal_thread_data['result_handler']

        msg = ('%s worker pool internal thread state:'
               ' (worker: %s, task: %s, result: %s)')
        args = (name,
                worker_handler,
                task_handler,
                result_handler)

        self.write_to_log(msg % args)

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
        idle_workers = []

        for worker_state in inspect_data:
            if worker_state['idle']:
                idle_workers.append(worker_state)
                continue

            if worker_state['start_time'] is None:
                continue

            spent = time.time() - worker_state['start_time']

            # Save us some disk space and sanity, only log worker state if it has
            # been running for at least 10 seconds
            if spent < 10:
                continue

            parts = []
            for arg in worker_state['args']:
                try:
                    arg_repr = repr(arg)
                except UnicodeEncodeError:
                    arg_str = smart_str_ignore(arg)
                else:
                    arg_str = smart_str_ignore(arg_repr)

                if len(arg_str) > 80:
                    arg_str = arg_str[:80] + "...'"

                parts.append(arg_str)

            args_str = ', '.join(parts)

            short_kwargs = {}
            for key, value in worker_state['kwargs']:
                try:
                    value_repr = repr(value)
                except UnicodeEncodeError:
                    value_str = smart_str_ignore(value)
                else:
                    value_str = smart_str_ignore(value_repr)

                if len(value_str) > 80:
                    value_str = value_str[:80] + "...'"

                short_kwargs[key] = value_str

            kwargs_str = smart_str_ignore(short_kwargs)

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

            trace = worker_state.get('trace', None)
            if trace is not None:
                message += '. Function call tree: %s' % trace

            self.write_to_log(message)

        #
        #   Write the idle workers all together at the end, this makes
        #   the log easier to read
        #
        for worker_state in idle_workers:
            message = 'Worker with ID %s(%s) is idle.'
            message %= (worker_state['name'], worker_state['worker_id'])
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
