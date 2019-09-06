"""
manager.py

Copyright 2006 Andres Riancho

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
import Queue
import threading

from multiprocessing.dummy import Process
from functools import wraps

from w3af import ROOT_PATH
from w3af.core.controllers.misc.factory import factory
from w3af.core.controllers.threads.threadpool import Pool
from w3af.core.controllers.core_helpers.consumers.constants import POISON_PILL
from w3af.core.controllers.threads.silent_joinable_queue import SilentJoinableQueue
from w3af.core.data.constants.encodings import UTF8


def start_thread_on_demand(func):
    """
    Given that the output manager has been migrated into a producer/consumer
    model, the messages that are sent to it are added to a Queue and printed
    "when the om thread gets its turn".

    The issue with this is that NOT EVERYTHING YOU SEE IN THE CONSOLE is
    printed using the om (see functions below), which ends up with unordered
    messages printed to the console.
    """
    @wraps(func)
    def od_wrapper(*args, **kwds):
        from w3af.core.controllers.output_manager import manager

        if manager.is_alive():
            return func(*args, **kwds)

        with OutputManager.start_lock:
            try:
                manager.start()
            except RuntimeError:
                # is_alive() might say that the process is NOT alive when:
                #   * We just created the OutputManager instance
                #   * The instance was created, started and joined
                #
                # In the second case, we can't start() it again and thus we'll
                # get a RuntimeError
                #
                # https://github.com/andresriancho/w3af/issues/7453
                # https://github.com/andresriancho/w3af/issues/5354
                pass

        return func(*args, **kwds)

    return od_wrapper


class OutputManager(Process):
    """
    This class manages output. It has a list of output plugins and sends the
    messages to every plugin on that list.

    Logs are sent to the "out" instance (see module level variable) and using
    a queue we forward the messages to this object which will be calling the
    output plugins.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    # If the FLUSH_TIMEOUT is larger (60 seconds for example) the time it takes
    # for the plugin to process all the messages / vulnerabilities in a call to
    # flush() will be larger, because w3af will (most likely) have found more
    # vulnerabilities. So we're calling the flush() method more often and having
    # shorter calls to flush() than before.
    FLUSH_TIMEOUT = 30

    # To prevent locks this always needs to be larger than the output plugins
    # available in the w3af framework
    WORKER_THREADS = 10

    # Thread locking to avoid starting the om many times from different threads
    start_lock = threading.RLock()

    def __init__(self):
        super(OutputManager, self).__init__(name='OutputManager')
        self.daemon = True
        self.name = 'OutputManager'

        # User configured options
        self._output_plugin_instances = []
        self._output_plugin_names = []
        self._plugin_options = {}

        # Internal variables
        self.in_queue = SilentJoinableQueue()
        self._w3af_core = None
        self._last_output_flush = None
        self._is_shutting_down = False
        self._worker_pool = self.get_worker_pool()

    def set_w3af_core(self, w3af_core):
        self._w3af_core = w3af_core

    def get_worker_pool(self):
        return Pool(self.WORKER_THREADS,
                    worker_names='OutputManagerWorkerThread',
                    max_queued_tasks=self.WORKER_THREADS * 10)

    def get_in_queue(self):
        """
        The output sinks need this queue, they will send the messages directly
        to it from different threads/processes. Then the main process will
        get the log messages and process them in the run() method below.

        :return: A multiprocessing Queue
        """
        return self.in_queue

    def start(self):
        with self.start_lock:
            if not self.is_alive():
                super(OutputManager, self).start()

    def run(self):
        """
        This method is one of the most important ones in the class, since it
        will consume the work units from the queue and send them to the plugins
        """
        while True:
            try:
                work_unit = self.in_queue.get(timeout=self.FLUSH_TIMEOUT)
            except Queue.Empty:
                self.flush_plugin_output()
                continue

            except EOFError:
                # The queue which we're consuming ended abruptly, this is
                # usually a side effect of the process ending and
                # multiprocessing not handling things cleanly
                try:
                    self.in_queue.task_done()
                finally:
                    break

            if work_unit == POISON_PILL:
                # This is added at fresh_output_manager_inst
                self.in_queue.task_done()
                break

            elif self._is_shutting_down:
                # Just ignore the log message if we're in the process of shutting
                # down the output manager. This prevents some race conditions where
                # messages are processed after plugins are ended
                self.in_queue.task_done()

            else:
                args, kwargs = work_unit
                #
                #    Please note that error handling is done inside:
                #        _call_output_plugins_action
                #
                self._call_output_plugins_action(*args, **kwargs)

                self.in_queue.task_done()

            # Now that the new message has been processed by the output plugins
            # we flush the output (if needed)
            self.flush_plugin_output()

    def flush_plugin_output(self):
        """
        Call flush() on all plugins so they write their data to the external
        file(s) / socket(s) if they want to. This is useful when the scan
        takes a lot of time to complete.

        By default output plugins have a no-op implementation for flush(), but
        plugins like xml_file and csv_file will write to the user configured
        files when called.

        Only flush once every FLUSH_TIMEOUT seconds.

        :see: https://github.com/andresriancho/w3af/issues/6726
        :return: None
        """
        if not self.should_flush():
            return

        pool = self._worker_pool
        if pool.is_closed():
            return

        self.update_last_output_flush()

        for o_plugin in self._output_plugin_instances:
            pool.apply_async(func=self.__inner_flush_plugin_output,
                             args=(o_plugin,))

    def __inner_flush_plugin_output(self, o_plugin):
        """
        This method is meant to be run in a thread. We run flush() in a thread
        to avoid some issues where a long time to process the xml flush was
        impacting the messages from being written to the text file.

        When we run the flush() call make sure that we're not calling flush again
        on the same plugin. This will prevent multiple simultaneous calls to flush
        running in an endless way during the scan.

        :param o_plugin: The output plugin to run
        :return: None, we don't care about the output of this method.
        """
        # If for some reason the output plugin takes a lot of time to run
        # and the output manager calls flush() for a second time while
        # we're still running the first call, just ignore.
        if o_plugin.is_running_flush:
            import w3af.core.controllers.output_manager as om

            msg = ('The %s plugin is still running flush(), the output'
                   ' manager will not call flush() again to give the'
                   ' plugin time to finish.')
            args = (o_plugin.get_name(),)
            om.out.debug(msg % args)
            return

        #
        #   Plugins might crash when calling .flush(), a good example was
        #   the unicodedecodeerror found in xml_file which was triggered
        #   when the findings were written to file.
        #
        start_time = time.time()
        o_plugin.is_running_flush = True

        try:
            o_plugin.flush()
        except Exception, exception:
            self._handle_output_plugin_exception(o_plugin, exception)
        finally:
            o_plugin.is_running_flush = False

            spent_time = time.time() - start_time
            args = (o_plugin.get_name(), spent_time)

            import w3af.core.controllers.output_manager as om
            om.out.debug('%s.flush() took %.2fs to run' % args)

    def _handle_output_plugin_exception(self, o_plugin, exception):
        if self._w3af_core is None:
            return

        # Smart error handling, much better than just crashing.
        # Doing this here and not with something similar to:
        # sys.excepthook = handle_crash because we want to handle
        # plugin exceptions in this way, and not framework
        # exceptions
        #
        # FIXME: I need to import this here because of the awful
        #        singletons I use all over the framework. If imported
        #        at the top, they will generate circular import errors
        from w3af.core.controllers.core_helpers.status import CoreStatus

        class FakeStatus(CoreStatus):
            pass

        status = FakeStatus(self._w3af_core)
        status.set_current_fuzzable_request('output', 'n/a')
        status.set_running_plugin('output', o_plugin.get_name(),
                                  log=False)

        exec_info = sys.exc_info()
        enabled_plugins = 'n/a'
        self._w3af_core.exception_handler.handle(status, exception,
                                                 exec_info,
                                                 enabled_plugins)

    def should_flush(self):
        """
        :return: True if we have to flush the output
        """
        if self._last_output_flush is None:
            return True

        time_diff = time.time() - self._last_output_flush
        if time_diff >= self.FLUSH_TIMEOUT:
            return True

        return False

    def update_last_output_flush(self):
        self._last_output_flush = time.time()

    def end_output_plugins(self):
        self.process_all_messages()

        # Wait for any calls to flush() which might be running
        self._worker_pool.close()
        self._worker_pool.join()

        # Now call end() on all plugins
        self.__end_output_plugins_impl()

    @start_thread_on_demand
    def process_all_messages(self):
        """
        Blocks until all messages are processed
        """
        self.in_queue.join()

    def __end_output_plugins_impl(self):
        #
        # Setting self._is_shutting_down here guarantees that no more
        # messages are going to be processed by this output manager instance
        # until we set the attribute to False again.
        #
        # This fixes an issue with "I/O operation on closed file" which was
        # reported multiple times over the years. The race condition happen
        # when a message was processed after the plugins were ended.
        #
        # By doing this we might lose some messages, BUT I reviewed the code
        # to make sure end_output_plugins() is called at the end of the scan
        # and that no "important messages" would be lost.
        #
        self._is_shutting_down = True

        # Call .end() on all plugin instances. Save the exceptions (if any)
        # and raise the first one.
        #
        # We want all plugin instances to get the chance to run their .end()
        # and we also don't want to ignore exceptions
        exc_info = None

        for o_plugin in self._output_plugin_instances:
            try:
                o_plugin.end()
            except:
                exc_info = sys.exc_info()
                continue

        if exc_info:
            # pylint: disable=E0702
            raise exc_info
            # pylint: enable=E0702

        # This is a neat trick which basically removes all plugin references
        # from memory. Those plugins might have pointers to memory parts that
        # are not required anymore (since someone is calling end_output_plugins
        # which indicates that the scan is done).
        #
        # If the console plugin was enabled, I re-enable it since I don't want
        # to loose the capability of seeing my log messages in the console
        #
        # Remember that the gtk_output plugin disappeared and was moved to
        # core.ui.output
        currently_enabled_plugins = self.get_output_plugins()
        keep_enabled = [pname for pname in currently_enabled_plugins
                        if pname in ('console',)]
        self.set_output_plugins(keep_enabled)

        # Process messages again, we removed the plugins which were ended
        self._is_shutting_down = False

    @start_thread_on_demand
    def log_enabled_plugins(self, enabled_plugins, plugins_options):
        """
        This method logs to the output plugins the enabled plugins and their
        configuration.

        :param enabled_plugins: As returned by w3afCore's
                                get_all_enabled_plugins() looks similar to:
                   {'audit':[],'grep':[],'bruteforce':[],'crawl':[],...}

        :param plugins_options: As defined in the w3afCore, looks similar to:
                   {'audit':{},'grep':{},'bruteforce':{},'crawl':{},...}
        """
        for o_plugin in self._output_plugin_instances:
            o_plugin.log_enabled_plugins(enabled_plugins, plugins_options)

    def _call_output_plugins_action(self, action_name, *args, **kwds):
        """
        Internal method used to invoke the requested action on each plugin
        in the output plugin list.
        
        A caller to any of the METHODS can specify that the call he's doing
        should NOT go to a specific plugin set specified in the ignore_plugins
        keyword argument.
        
        """
        encoded_params = []

        # http://docs.python.org/2/howto/unicode.html
        #
        # The most important tip is:
        #     Software should only work with Unicode strings internally,
        #     converting to a particular encoding on output.
        #
        # Given that we don't want to convert to utf8 inside every plugin
        # before sending to a file, we do it here
        for arg in args:
            if isinstance(arg, unicode):
                arg = arg.encode(UTF8, 'replace')

            encoded_params.append(arg)

        args = tuple(encoded_params)
        
        # A caller to any of the METHODS can specify that the call he's doing
        # should NOT go to a specific plugin set specified in the ignore_plugins
        # keyword argument
        #
        # We do a pop() here because the plugin method doesn't really receive
        # the ignored plugin set, we just filter them at this level.
        #
        # This is used (mostly) for reporting errors generated in output
        # plugins without having the risk of generating a cascading effect
        # that would make the output manager go crazy, usually that's done
        # by doing something like:
        #
        #    om.out.error(msg, ignore_plugins=set([self.get_name()])
        #
        ignored_plugins = kwds.pop('ignore_plugins', set())

        for o_plugin in self._output_plugin_instances:
            
            if o_plugin.get_name() in ignored_plugins:
                continue
            
            try:
                opl_func_ptr = getattr(o_plugin, action_name)
                apply(opl_func_ptr, args, kwds)
            except Exception, exception:
                self._handle_output_plugin_exception(o_plugin, exception)

    def set_output_plugin_inst(self, output_plugin_inst):
        self._output_plugin_instances.append(output_plugin_inst)

    def get_output_plugin_inst(self):
        return self._output_plugin_instances
        
    def set_output_plugins(self, output_plugins):
        """
        :param output_plugins: A list with the names of Output Plugins that
                               will be used.
        :return: No value is returned.
        """
        self._output_plugin_instances = []
        self._output_plugin_names = output_plugins

        for plugin_name in self._output_plugin_names:
            self._add_output_plugin(plugin_name)

    def get_output_plugins(self):
        return self._output_plugin_names

    def set_plugin_options(self, plugin_name, plugin_options):
        """
        :param plugin_options: A tuple with a string and a dictionary
                                   with the options for a plugin. For example:\
                                   { console:{'verbose': True} }

        :return: No value is returned.
        """
        self._plugin_options[plugin_name] = plugin_options

    def _add_output_plugin(self, output_plugin_name):
        """
        Takes a string with the OutputPluginName, creates the object and
        adds it to the OutputPluginName

        :param output_plugin_name: The name of the plugin to add to the list.
        :return: No value is returned.
        """
        if output_plugin_name == 'all':
            file_list = os.listdir(os.path.join(ROOT_PATH, 'plugins', 'output'))

            sext = os.path.splitext
            str_req_plugins = [sext(f)[0] for f in file_list if sext(f)[1] == '.py']
            str_req_plugins.remove('__init__')

            for plugin_name in str_req_plugins:
                plugin = self._get_plugin_instance(plugin_name)
                self._output_plugin_instances.append(plugin)

        else:
            plugin = self._get_plugin_instance(output_plugin_name)
            self._output_plugin_instances.append(plugin)

    def _get_plugin_instance(self, plugin_name):
        plugin = factory('w3af.plugins.output.%s' % plugin_name)
        plugin.set_w3af_core(self._w3af_core)

        if plugin_name in self._plugin_options.keys():
            plugin.set_options(self._plugin_options[plugin_name])

        return plugin
