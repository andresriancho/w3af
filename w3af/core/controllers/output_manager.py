"""
output_manager.py

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
import functools
import os
import sys
import threading
import logging

from cPickle import PicklingError
from multiprocessing.dummy import Process

from w3af import ROOT_PATH
from w3af.core.controllers.misc.factory import factory
from w3af.core.controllers.core_helpers.consumers.constants import POISON_PILL
from w3af.core.data.constants.encodings import UTF8
from w3af.core.controllers.threads.silent_joinable_queue import SilentJoinableQueue

# https://pypi.python.org/pypi/stopit#logging
# The stopit named logger emits a warning each time a block of code execution
# exceeds the associated timeout. To turn logging off, just:
stopit_logger = logging.getLogger('stopit')
stopit_logger.setLevel(logging.ERROR)

# Thread locking to avoid starting the om many times from different threads
start_lock = threading.RLock()


def fresh_output_manager_inst():
    """
    Creates a new "manager" instance at the module level.

    :return: A reference to the newly created instance
    """
    global manager

    #
    #   Stop the old instance thread
    #
    if manager.is_alive():
        manager.in_queue.put(POISON_PILL)
        manager.join()

    #
    #   Create the new instance
    #
    manager = OutputManager()
    return manager


def log_sink_factory(om_queue):
    """
    Creates a new "out" instance at the module level.

    :return: A reference to the newly created instance
    """
    global out
    out = LogSink(om_queue)
    return out


def start_thread_on_demand(func):
    """
    Given that the output manager has been migrated into a producer/consumer
    model, the messages that are sent to it are added to a Queue and printed
    "when the om thread gets its turn".
    
    The issue with this is that NOT EVERYTHING YOU SEE IN THE CONSOLE is
    printed using the om (see functions below), which ends up with unordered
    messages printed to the console.
    """
    def od_wrapper(*args, **kwds):
        global start_lock
        with start_lock:
            if not manager.is_alive():
                manager.start()
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

    METHODS = (
        'debug',
        'information',
        'error',
        'vulnerability',
        'console',
        'log_http',
    )

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

    def set_w3af_core(self, w3af_core):
        self._w3af_core = w3af_core

    def get_in_queue(self):
        """
        The output sinks need this queue, they will send the messages directly
        to it from different threads/processes. Then the main process will
        get the log messages and process them in the run() method below.

        :return: A multiprocessing Queue
        """
        return self.in_queue

    def start(self):
        global start_lock
        with start_lock:
            if not self.is_alive():
                super(OutputManager, self).start()

    def run(self):
        """
        This method is one of the most important ones in the class, since it
        will consume the work units from the queue and send them to the plugins
        """
        while True:
            try:
                work_unit = self.in_queue.get()
            except EOFError:
                # The queue which we're consuming ended abruptly, this is
                # usually a side effect of the process ending and
                # multiprocessing not handling things cleanly
                break

            if work_unit == POISON_PILL:

                break

            else:
                args, kwds = work_unit
                #
                #    Please note that error handling is done inside:
                #        _call_output_plugins_action
                #
                apply(self._call_output_plugins_action, args, kwds)

                self.in_queue.task_done()

    def end_output_plugins(self):
        self.process_all_messages()
        self.__end_output_plugins_impl()

    @start_thread_on_demand
    def process_all_messages(self):
        """
        Blocks until all messages are processed
        """
        self.in_queue.join()

    def __end_output_plugins_impl(self):
        for o_plugin in self._output_plugin_instances:
            o_plugin.end()

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
            except Exception, e:
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
                from w3af.core.controllers.core_helpers.status import w3af_core_status

                class fake_status(w3af_core_status):
                    pass

                status = fake_status(self._w3af_core)
                status.set_current_fuzzable_request('output', 'n/a')
                status.set_running_plugin('output', o_plugin.get_name(),
                                          log=False)

                exec_info = sys.exc_info()
                enabled_plugins = 'n/a'
                self._w3af_core.exception_handler.handle(status, e,
                                                         exec_info,
                                                         enabled_plugins)

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
            str_req_plugins = [os.path.splitext(f)[0] for f in file_list
                               if os.path.splitext(f)[1] == '.py']
            str_req_plugins.remove('__init__')

            for plugin_name in str_req_plugins:
                plugin = factory('w3af.plugins.output.' + plugin_name)

                if plugin_name in self._plugin_options.keys():
                    plugin.set_options(self._plugin_options[plugin_name])

                # Append the plugin to the list
                self._output_plugin_instances.append(plugin)

        else:
            plugin = factory('w3af.plugins.output.' + output_plugin_name)
            if output_plugin_name in self._plugin_options.keys():
                plugin.set_options(self._plugin_options[output_plugin_name])

                # Append the plugin to the list
            self._output_plugin_instances.append(plugin)


class LogSink(object):
    """
    The log sink receives log messages in different threads/processes and sends
    them over a multiprocessing queue to the main process where they are handled
    by the output manager => output plugins.
    """
    def __init__(self, om_queue):
        super(LogSink, self).__init__()
        self.om_queue = om_queue

    def report_finding(self, info_inst):
        """
        The plugins call this in order to report an info/vuln object to the
        user. This is an utility function that simply calls information() or
        vulnerability() with the correct parameters, depending on the info_inst
        type and severity.

        :param info_inst: An Info class or subclass.
        """
        from w3af.core.data.kb.info import Info
        from w3af.core.data.kb.vuln import Vuln

        if isinstance(info_inst, Vuln):
            self.vulnerability(info_inst.get_desc(),
                               severity=info_inst.get_severity())

        elif isinstance(info_inst, Info):
            self.information(info_inst.get_desc())

    def _add_to_queue(self, *args, **kwds):
        try:
            self.om_queue.put((args, kwds))
        except IOError:
            print('LogSink queue communication lost. Some log messages will'
                  ' be lost.')

    def __getattr__(self, name):
        """
        This magic method replaces all the previous debug/information/error ones
        It will basically return a func pointer to
        self.add_to_queue('debug',  ...) where "..." is completed later by the
        caller.

        @see: http://docs.python.org/library/functools.html for help on partial.
        @see: METHODS defined at the top of this class
        """
        if name in OutputManager.METHODS:
            return functools.partial(self._add_to_queue, name)
        else:
            raise AttributeError("'LogSink' object has no attribute '%s'" % name)


# Create the default manager and out instances, we'll be creating others later
# most likely for the log sink, which will be replaced in each sub-process
manager = OutputManager()
out = log_sink_factory(manager.get_in_queue())