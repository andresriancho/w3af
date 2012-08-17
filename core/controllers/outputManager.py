'''
outputManager.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
import functools
import os
import sys
import threading
import Queue

from core.controllers.misc.factory import factory
from core.data.constants.encodings import UTF8
from core.controllers.coreHelpers.consumers.constants import POISON_PILL

def start_thread_on_demand(func):
    '''
    Given that the output manager has been migrated into a producer/consumer model,
    the messages that are sent to it are added to a Queue and printed "at a random time".
    The issue with this is that NOT EVERYTHING YOU SEE IN THE CONSOLE is printed
    using the om (see functions below), which ends up with unordered messages printed
    to the console. 
    '''
    def od_wrapper(*args, **kwds):
        if not out.is_alive():
            out.start()
        return func(*args, **kwds)
    return od_wrapper


class outputManager(threading.Thread):
    '''
    This class manages output. It has a list of output plugins and sends the 
    messages to every plugin on that list.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    METHODS = (
               'debug',
               'information',
               'error',
               'vulnerability',
               'console',
               'logHttp',
              )
        
    def __init__(self):
        super(outputManager, self).__init__()
        self.daemon = True
        
        # User configured options
        self._output_plugin_list = []
        self._output_plugins = []
        self._plugins_options = {}
        
        # Internal variables
        self._in_queue = Queue.Queue()
    
    def run(self):
        '''
        This method is one of the most important ones in the class, since it will
        consume the work units from the queue and send them to the plugins
        
        '''
        while True:
            work_unit = self._in_queue.get()
            
            if work_unit == POISON_PILL:
                
                break
            
            else:
                args, kwds = work_unit
                #
                #    Please note that error handling is done inside:
                #        _call_output_plugins_action
                #
                apply(self._call_output_plugins_action, args, kwds)
                
                self._in_queue.task_done()
    
    def end_output_plugins(self):
        self.process_all_messages()
        self.__end_output_plugins_impl()
    
    def process_all_messages(self):
        '''Blocks until all messages are processed'''
        self._in_queue.join()
    
    def _add_to_queue(self, *args, **kwds):
        self._in_queue.put( (args, kwds) )

    def __end_output_plugins_impl(self):
        for o_plugin in self._output_plugin_list:
            o_plugin.end()

        # This is a neat trick which basically removes all plugin references
        # from memory. Those plugins might have pointers to memory parts that
        # are not required anymore (since someone is calling end_output_plugins
        # which indicates that the scan is done).
        #
        # If the console or gtk_output plugins were enabled, I re-enable them
        # since I don't want to loose the capability of seeing my log messages
        # in the linux console or the message box in the GTK ui.
        currently_enabled_plugins = self.get_output_plugins()
        keep_enabled = [pname for pname in currently_enabled_plugins 
                        if pname in ('console', 'gtk_output')]
        self.set_output_plugins( keep_enabled )
            
    @start_thread_on_demand
    def log_enabled_plugins(self, enabled_plugins, plugins_options):
        '''
        This method logs to the output plugins the enabled plugins and their
        configuration.
        
        @param enabled_plugins: As returned by w3afCore's
                                getAllEnabledPlugins() looks similar to:
                   {'audit':[],'grep':[],'bruteforce':[],'crawl':[],...}
        
        @param plugins_options: As defined in the w3afCore, looks similar to: 
                   {'audit':{},'grep':{},'bruteforce':{},'crawl':{},...}
        '''
        for o_plugin in self._output_plugin_list:
            o_plugin.log_enabled_plugins(enabled_plugins, plugins_options)
    
    def _call_output_plugins_action(self, actionname, *args, **kwds):
        '''
        Internal method used to invoke the requested action on each plugin
        in the output plugin list.
        '''
        encoded_params = []
        
        for arg in args:
            if isinstance(arg, unicode):
                arg = arg.encode(UTF8, 'replace')
            
            encoded_params.append( arg )
        
        args = tuple(encoded_params)
          
        for o_plugin in self._output_plugin_list:
            try:
                opl_func_ptr = getattr(o_plugin, actionname)
                apply(opl_func_ptr, args, kwds)
            except Exception, e:
                # Smart error handling, much better than just crashing.
                # Doing this here and not with something similar to:
                # sys.excepthook = handle_crash because we want to handle
                # plugin exceptions in this way, and not framework 
                # exceptions
                #
                # FIXME: I need to import these here because of the awful
                #        singletons I use all over the framework. If imported
                #        at the top, they will generate circular import errors
                from core.controllers.coreHelpers.exception_handler import exception_handler
                from core.controllers.coreHelpers.status import w3af_core_status
                
                class fake_status(w3af_core_status):
                    pass
    
                status = fake_status()
                status.set_running_plugin( o_plugin.getName(), log=False )
                status.set_phase( 'output' )
                status.set_current_fuzzable_request( 'n/a' )
                
                exec_info = sys.exc_info()
                enabled_plugins = 'n/a'
                exception_handler.handle( status, e , exec_info, enabled_plugins )
    
    def set_output_plugins(self, outputPlugins):
        '''
        @parameter outputPlugins: A list with the names of Output Plugins that
                                  will be used.
        @return: No value is returned.
        '''     
        self._output_plugin_list = []
        self._output_plugins = outputPlugins
        
        for pluginName in self._output_plugins:
            out._add_output_plugin(pluginName)  
    
    def get_output_plugins(self):
        return self._output_plugins
    
    def set_plugin_options(self, pluginName, PluginsOptions):
        '''
        @parameter PluginsOptions: A tuple with a string and a dictionary
                                   with the options for a plugin. For example:\
                                   { console:{'verbose': True} }
            
        @return: No value is returned.
        '''
        self._plugins_options[pluginName] = PluginsOptions
        
    def _add_output_plugin(self, OutputPluginName):
        '''
        Takes a string with the OutputPluginName, creates the object and
        adds it to the OutputPluginName
        
        @parameter OutputPluginName: The name of the plugin to add to the list.
        @return: No value is returned.
        '''
        if OutputPluginName == 'all':
            fileList = os.listdir(os.path.join('plugins', 'output'))    
            strReqPlugins = [os.path.splitext(f)[0] for f in fileList
                                            if os.path.splitext(f)[1] == '.py']
            strReqPlugins.remove ('__init__')
            
            for pluginName in strReqPlugins:
                plugin = factory('plugins.output.' + pluginName)
                
                if pluginName in self._plugins_options.keys():
                    plugin.setOptions(self._plugins_options[pluginName])
                
                # Append the plugin to the list
                self._output_plugin_list.append(plugin)
        
        else:
            plugin = factory('plugins.output.' + OutputPluginName)
            if OutputPluginName in self._plugins_options.keys():
                plugin.setOptions(self._plugins_options[OutputPluginName])

                # Append the plugin to the list
            self._output_plugin_list.append(plugin)    
    
    @start_thread_on_demand
    def __getattr__(self, name):
        '''
        This magic method replaces all the previous debug/information/error... ones.
        It will basically return a func pointer to self.add_to_queue('debug', ...)
        where ... is completed later by the caller.
        
        @see: http://docs.python.org/library/functools.html for help on partial.
        @see: METHODS defined at the top of this class 
        '''
        if name in self.METHODS:
            return functools.partial(self._add_to_queue, name)
        else:
            raise AttributeError("'outputManager' object has no attribute '%s'"
                                 % name)

out = outputManager()
