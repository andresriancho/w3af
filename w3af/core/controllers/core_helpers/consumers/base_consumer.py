"""
base_consumer.py

Copyright 2012 Andres Riancho

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
import time

from Queue import Empty
from functools import wraps
from multiprocessing.dummy import Process

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.exception_handling.helpers import pprint_plugins
from w3af.core.controllers.core_helpers.exception_handler import ExceptionData
from w3af.core.controllers.core_helpers.status import CoreStatus
from w3af.core.controllers.core_helpers.consumers.constants import POISON_PILL
from w3af.core.controllers.threads.threadpool import Pool
from w3af.core.data.misc.cached_queue import CachedQueue


def task_decorator(method):
    """
    Makes sure that for each task we call _add_task() and _task_done()
    which will avoid some ugly race conditions.
    """
    
    @wraps(method)
    def _wrapper(self, *args, **kwds):
        rnd_id = os.urandom(32).encode('hex')
        function_id = '%s_%s' % (method.__name__, rnd_id)

        self._add_task(function_id)

        try:
            result = method(self, function_id, *args, **kwds)
        except:
            self._task_done(function_id)
            raise
        else:
            self._task_done(function_id)
            return result
    
    return _wrapper


# pylint: disable=E1120
class BaseConsumer(Process):
    """
    Consumer thread that takes fuzzable requests from a Queue that's populated
    by the crawl plugins and identified vulnerabilities by performing various
    requests.
    """

    THREAD_POOL_SIZE = 10

    def __init__(self, consumer_plugins, w3af_core, thread_name,
                 create_pool=True, max_pool_queued_tasks=0,
                 max_in_queue_size=0, thread_pool_size=None):
        """
        :param consumer_plugins: Instances of base_consumer plugins in a list
        :param w3af_core: The w3af core that we'll use for status reporting
        :param thread_name: How to name the current thread, eg. Auditor
        :param create_pool: True to create a worker pool for this consumer
        """
        super(BaseConsumer, self).__init__(name='%sController' % thread_name)

        self.in_queue = CachedQueue(maxsize=max_in_queue_size,
                                    name=thread_name + 'In')

        #
        # Crawl and infrastructure plugins write to this queue using:
        #
        #   self.output_queue.put(fuzz_req)
        #
        # The strategy will read items from this queue in a tight loop using:
        #
        #   result_item = url_producer.get_result(timeout=0.1)
        #
        # And write them to self.in_queue (defined above) for all the url consumers
        #
        # Since this queue is read in a tight loop, items that are written here
        # will, in theory, not stay in memory for long.
        #
        # Also, items written here are fuzzable requests, which shouldn't use a lot
        # of memory.
        #
        # The only scenario I can think of where this queue is full of items
        # is one where the strategy loop is slow / delayed and the crawl plugins
        # are all findings many new URLs and forms.
        #
        # Tests showed something like this for a common site:
        #
        #   [Thu Feb 15 16:45:36 2018 - debug] CachedQueue.get() ... CrawlInfraOut DiskDict size is 19.
        #   [Thu Feb 15 16:45:36 2018 - debug] CachedQueue.get() ... CrawlInfraOut DiskDict size is 28.
        #   [Thu Feb 15 16:45:37 2018 - debug] CachedQueue.get() ... CrawlInfraOut DiskDict size is 27.
        #   ...
        #   [Thu Feb 15 16:45:52 2018 - debug] CachedQueue.get() ... CrawlInfraOut DiskDict size is 1.
        #
        # This was with a max_in_queue_size of 100 set for the CachedQueue defined below.
        #
        # Meaning that:
        #       * There were 119 items in the queue (100 in memory) in the first log line
        #       * Also at 16:45:36, there were 128 items in the queue (100 in memory)
        #       * It took 16 seconds to consume 28 items from the queue (from second 36 to second 52)
        #
        # This surprises me a little bit. I expected this queue to have less items in memory.
        # Since I want to remove the memory usage in the framework, I'm going to reduce the
        # maxsize sent to this CachedQueue to 75
        #
        # But just in case I'm using a CachedQueue!
        self._out_queue = CachedQueue(maxsize=75, name=thread_name + 'Out')

        self._thread_name = thread_name
        self._consumer_plugins = consumer_plugins
        self._w3af_core = w3af_core
        self._observers = []

        self._tasks_in_progress = {}
        self._poison_pill_sent = False
        self._has_finished = False

        self._threadpool = None

        if create_pool:
            self._threadpool = Pool(thread_pool_size or self.THREAD_POOL_SIZE,
                                    worker_names='%sWorker' % thread_name,
                                    max_queued_tasks=max_pool_queued_tasks)

    def get_pool(self):
        return self._threadpool

    def get_name(self):
        raise NotImplementedError

    def set_has_finished(self):
        self._has_finished = True
        self._w3af_core.strategy.clear_queue_speed_data()

    def run(self):
        """
        Consume the queue items, sending them to the plugins which are then
        going to find vulnerabilities, new URLs, etc.
        """
        while True:

            try:
                work_unit = self.in_queue.get()
            except KeyboardInterrupt:
                # https://github.com/andresriancho/w3af/issues/9587
                #
                # If we don't do this, the thread will die and will never
                # process the POISON_PILL, which will end up in an endless
                # wait for .join()
                continue

            if work_unit == POISON_PILL:
                try:
                    self._process_poison_pill()
                except Exception, e:
                    msg = 'An exception was found while processing poison pill: "%s"'
                    om.out.debug(msg % e)
                finally:
                    self.in_queue.task_done()
                    break

            else:
                # pylint: disable=E1120
                try:
                    self._consume_wrapper(work_unit)
                finally:
                    self.in_queue.task_done()

            self._log_queue_sizes()

    def _log_queue_sizes(self):
        if not self._poison_pill_sent:
            return

        msg = ('The %s input queue received the POISON_PILL. Processing %s'
               ' tasks from input queue and %s tasks from output queue before'
               ' breaking out of the loop')
        args = (self._thread_name,
                self.in_queue.qsize(),
                self.out_queue.qsize())
        om.out.debug(msg % args)

        if len(self._tasks_in_progress):
            msg = 'The %s consumer has %s tasks in progress'
            args = (self._thread_name, len(self._tasks_in_progress))
            om.out.debug(msg % args)

        if self._threadpool is not None:

            msg = ('The %s consumer pool has %s tasks in the input queue'
                   ' and %s tasks in the output queue')
            args = (self._thread_name,
                    self._threadpool.get_inqueue().qsize(),
                    self._threadpool.get_outqueue().qsize())
            om.out.debug(msg % args)

    def _process_poison_pill(self):
        om.out.debug('Processing POISON_PILL in %s' % self._thread_name)

        try:
            self._shutdown_threadpool()
        except:
            # All the logging is done inside the method, an empty
            # except clause is acceptable in this case
            pass

        try:
            self._call_teardown()
        except:
            # All the logging is done inside the method, an empty
            # except clause is acceptable in this case
            pass
        finally:
            self._out_queue.put(POISON_PILL)
            self.set_has_finished()

    def _shutdown_threadpool(self):
        if self._threadpool is None:
            msg = '%s pool is None. No shutdown required.'
            om.out.debug(msg % self._thread_name)
            return

        #
        # Close the pool and wait for everyone to finish
        #
        # Quickly set the threadpool attribute to None to prevent other calls
        # to this method from running close() or join() twice on the same pool
        # This should never happen (only one POISON_PILL should ever be sent
        # to a queue) but...
        #
        pool = self._threadpool
        self._threadpool = None

        msg_fmt = 'Exception found while %s pool in %s consumer: "%s"'

        try:
            pool.close()
        except Exception, e:
            args = ('closing', self.get_name(), e)
            om.out.debug(msg_fmt % args)

        msg = '%s pool is closed'
        om.out.debug(msg % self._thread_name)

        try:
            pool.join()
        except Exception, e:
            args = ('joining', self.get_name(), e)
            om.out.debug(msg_fmt % args)

            # First try to call join(), which is nice and waits for all the
            # tasks to complete. If that fails, then call terminate()
            try:
                pool.terminate()
            except Exception, e:
                args = ('terminating', self.get_name(), e)
                om.out.debug(msg_fmt % args)
            else:
                msg = '%s pool has been terminated after failed call to join'
                om.out.debug(msg % self._thread_name)

        msg = '%s pool has been joined'
        om.out.debug(msg % self._thread_name)

    def _call_teardown(self):
        # Finish this consumer and everyone consuming the output
        try:
            self._teardown()
        except Exception, e:
            msg = 'Exception found while calling teardown() in %s consumer: "%s"'
            args = (self.get_name(), e)
            om.out.debug(msg % args)

    def get_running_task_count(self):
        """
        :return: The number of tasks which are currently running in the
                 threadpool. This is commonly used for measuring ETA.
        """
        if self._threadpool is None:
            return 0

        return self._threadpool.get_running_task_count()

    def _teardown(self):
        raise NotImplementedError

    def _consume(self, work_unit):
        raise NotImplementedError

    def has_finished(self):
        return self._has_finished

    @task_decorator
    def _consume_wrapper(self, function_id, work_unit):
        """
        Just makes sure that all _consume methods are decorated as tasks.
        """
        return self._consume(work_unit)

    def _task_done(self, function_id):
        """
        The task_in_progress_counter is needed because we want to know if the
        consumer is processing something and let it finish. It is mainly used
        in the has_pending_work().

        For example:

            * You can have pending work if there are items in the input_queue

            * You can have pending work if there are still items to be read from
            the output_queue by one of the consumers that reads our output.

            * You can have pending work when there are no items in input_queue
            and no items in output_queue but the threadpool inside the consumer
            is processing something. This situation is handled by the
            self._tasks_in_progress attribute and the _add_task and
            _task_done methods.

        So, for each _add_task() there has to be a _task_done() even if the
        task ends in an error or exception.
        
        Recommendation: Do NOT set the callback for apply_async to call
        _task_done, the Python2.7 pool implementation won't call it if the
        function raised an exception and you'll end up with tasks in progress
        that finished with an exception.
        """
        try:
            self._tasks_in_progress.pop(function_id)
        except KeyError:
            raise AssertionError('The function with ID %s was not found!' % function_id)

    def _add_task(self, function_id):
        """
        :param function_id: Just for debugging

        @see: _task_done()'s documentation.
        """
        self._tasks_in_progress[function_id] = 1

    def in_queue_put(self, work, force=False):
        """
        Add work to the queue

        :param work: Work item
        :param force: Add to the queue even when the poison pill was already
                      sent, this should NEVER be used unless you know what
                      you are doing!

        :return: True if the task was added to the queue
        """
        if work is None:
            return

        # Force the queue not to accept anything after POISON_PILL is sent.
        #
        # If anything is put to the queue after POISON_PILL, a race condition
        # might happen and the consumer might never stop
        #
        # https://github.com/andresriancho/w3af/pull/16063
        if self._poison_pill_sent and not force:
            return
        
        return self.in_queue.put(work)

    def in_queue_put_iter(self, work_iter):
        if work_iter is not None:
            for work in work_iter:
                self.in_queue_put(work)

    def has_pending_work(self):
        """
        @see: _task_done() documentation

        :return: True if the in_queue_size is != 0 OR if one of the pool workers
                 is still doing something that might impact on out_queue.
        """
        if self.in_queue_size() > 0:
            return True

        if self.out_queue.qsize() > 0:
            return True

        if len(self._tasks_in_progress) > 0:
            return True

        # This is a special case which loosely translates to: "If there are any
        # pending tasks in the threadpool, even if they haven't yet called the
        # _add_task method, we know we have pending work to do".
        if self._threadpool is not None:

            if self._threadpool._inqueue.qsize() > 0:
                return True

            if self._threadpool._outqueue.qsize() > 0:
                return True
        
        return False

    @property
    def out_queue(self):
        # This output queue can contain one of the following:
        #    * POISON_PILL
        #    * (plugin_name, fuzzable_request, AsyncResult)
        #    * An ExceptionData instance
        return self._out_queue

    def in_queue_size(self):
        return self.in_queue.qsize()

    def send_poison_pill(self):
        if self._poison_pill_sent:
            return

        # https://github.com/andresriancho/w3af/issues/9587
        # let put() know that all new tasks should be ignored
        self._poison_pill_sent = True

        # send the poison pill
        self.in_queue_put(POISON_PILL, force=True)

        msg = 'Sent POISON_PILL to the %s consumer in_queue'
        om.out.debug(msg % self._thread_name)

    def join(self):
        """
        Poison the loop and wait for all queued work to finish this might take
        some time to process.
        """
        msg = 'Called %s consumer join()'
        om.out.debug(msg % self._thread_name)

        start_time = time.time()

        if not self.is_alive():
            # This return has a long history, follow it here:
            # https://github.com/andresriancho/w3af/issues/1172
            msg = 'The %s consumer thread was not alive'
            om.out.debug(msg % self._thread_name)
            return

        self.send_poison_pill()

        msg = 'Calling join() on %s.in_queue (qsize:%s)'
        args = (self._thread_name, self.in_queue.qsize())
        om.out.debug(msg % args)

        self.in_queue.join()

        msg = 'Successfully joined the %s consumer in_queue'
        om.out.debug(msg % self._thread_name)

        self._shutdown_threadpool()

        spent_time = time.time() - start_time
        om.out.debug('%s took %.2f seconds to join()' % (self._thread_name, spent_time))

    def _clear_input_output_queues(self):
        #
        # Remove all queued tasks from the input queue to prevent new tasks
        # from being started
        #
        while True:
            try:
                self.in_queue.get_nowait()
            except Empty:
                break
            else:
                self.in_queue.task_done()

        self._log_queue_sizes()

        #
        # Remove all queued tasks from the output queue to prevent the results
        # from making it to the core, which could trigger other tasks
        #
        while True:
            try:
                self.out_queue.get_nowait()
            except Empty:
                break
            else:
                self.out_queue.task_done()

        self._log_queue_sizes()

    def terminate(self):
        """
        Remove all queued work from in_queue and poison the loop so the consumer
        exits. Should be very fast and called only if we don't care about the
        queued work anymore (ie. user clicked stop in the UI).
        """
        self._clear_input_output_queues()

        # This call to join should be super-fast, there are no tasks in the
        # queues: only need to wait for the tasks that are currently running
        # in the threadpool
        self.join()

    def get_result(self, timeout=0.5):
        """
        :return: The first result from the output Queue.
        """
        return self._out_queue.get(timeout=timeout)

    def get_result_nowait(self):
        return self._out_queue.get_nowait()

    def handle_exception(self, phase, plugin_name, fuzzable_request, _exception):
        """
        Get the exception information, and put it into the output queue
        then, the strategy will get the items from the output queue and
        handle the exceptions.

        :param plugin_name: The plugin that generated the exception
        :param fuzzable_request: The fuzzable request that was sent as input to
                                 the plugin when the exception was raised
        :param _exception: The exception object
        """
        except_type, except_class, tb = sys.exc_info()
        enabled_plugins = pprint_plugins(self._w3af_core)

        status = CoreStatus(self._w3af_core)
        status.set_running_plugin(phase, plugin_name, log=False)
        status.set_current_fuzzable_request(phase, fuzzable_request)

        exception_data = ExceptionData(status,
                                       _exception,
                                       tb,
                                       enabled_plugins,
                                       store_tb=False)
        self._out_queue.put(exception_data)

    def add_observer(self, observer):
        self._observers.append(observer)

    def _log_end_took(self, msg_fmt, start_time, plugin):
        spent_time = time.time() - start_time
        args = (spent_time, plugin.get_name())
        om.out.debug(msg_fmt % args)
