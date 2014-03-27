"""
plugins.py

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
import sys
import threading
import Queue

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om

from w3af.core.data.options.option_list import OptionList
from w3af.core.controllers.configurable import Configurable
from w3af.core.controllers.threads.threadpool import return_args
from w3af.core.controllers.exceptions import ScanMustStopOnUrlError


class Plugin(Configurable):
    """
    This is the base class for ALL plugins, all plugins should inherit from it
    and implement the following method :
        1. get_plugin_deps()

    Please note that this class is a configurable object, so it must implement:
        1. set_options( OptionList )
        2. get_options()

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        """
        Create some generic attributes that are going to be used by most plugins.
        """
        self._uri_opener = None
        self.worker_pool = None
        
        self.output_queue = Queue.Queue()
        self._plugin_lock = threading.RLock()

    def set_worker_pool(self, worker_pool):
        """
        Sets the worker pool (at the moment of writing this is a thread pool)
        that will be used by the plugin to send requests using different
        threads.
        """
        self.worker_pool = worker_pool

    def set_url_opener(self, urlOpener):
        """
        This method should not be overwritten by any plugin (but you are free
        to do it, for example a good idea is to rewrite this method to change
        the UrlOpener to do some IDS evasion technique).

        This method takes a CustomUrllib object as parameter and assigns it
        to itself. Then, on the testUrl method you use
        self.CustomUrlOpener._custom_urlopen(...)
        to open a Url and you are sure that the plugin is using the user
        supplied settings (proxy, user agent, etc).

        :return: No value is returned.
        """
        self._uri_opener = UrlOpenerProxy(urlOpener, self)

    def set_options(self, options_list):
        """
        Sets the Options given on the OptionList to self. The options are the
        result of a user entering some data on a window that was constructed
        using the options that were retrieved from the plugin using get_options()

        This method must be implemented in every plugin that wishes to have user
        configurable options.

        :return: No value is returned.
        """
        pass

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()
        return ol

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be
                 run before the current one. Only plugins with dependencies
                 should override this method.
        """
        return []

    def get_desc(self):
        """
        :return: A description of the plugin.
        """
        if self.__doc__ is not None:
            tmp = self.__doc__.replace('    ', '')
            
            res = ''.join(l for l in tmp.split('\n') if l != '' and
                          not l.startswith(':'))
        else:
            res = 'No description available for this plugin.'
        return res

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        raise NotImplementedError(
            'Plugin is not implementing required method get_long_desc')

    def kb_append_uniq(self, location_a, location_b, info, filter_by='VAR'):
        """
        kb.kb.append_uniq a vulnerability to the KB
        """
        added_to_kb = kb.kb.append_uniq(location_a, location_b, info,
                                        filter_by=filter_by)

        if added_to_kb:
            om.out.report_finding(info)
        
    def kb_append(self, location_a, location_b, info):
        """
        kb.kb.append a vulnerability to the KB
        """
        kb.kb.append(location_a, location_b, info)
        om.out.report_finding(info)
        
    def __eq__(self, other):
        """
        This function is called when extending a list of plugin instances.
        """
        return self.__class__.__name__ == other.__class__.__name__

    def end(self):
        """
        This method is called by w3afCore to let the plugin know that it wont
        be used anymore. This is helpfull to do some final tests, free some
        structures, etc.
        """
        pass

    def get_type(self):
        return 'plugin'

    def get_name(self):
        return self.__class__.__name__

    def handle_url_error(self, url_error):
        """
        Handle UrlError exceptions raised when requests are made.
        Subclasses should redefine this method for a more refined
        behavior and must respect the return value format.

        :param url_error: ScanMustStopOnUrlError exception instance
        :return: (stopbubbling, result). The 1st is a boolean value
            that indicates the caller if the original error should
            stop bubbling or not. The 2nd is the result to be
            returned by the caller. Note that only makes sense
            when `stopbubbling` is True.
        """
        om.out.error('There was an error while requesting "%s". Reason: %s' %
                     (url_error.req.get_full_url(), url_error.msg))
        return False, None

    def _send_mutants_in_threads(self, func, iterable, callback, **kwds):
        """
        Please note that this method blocks from the caller's point of view
        but performs all the HTTP requests in parallel threads.
        """
        func = return_args(func, **kwds)
        imap_unordered = self.worker_pool.imap_unordered

        for (mutant,), http_response in imap_unordered(func, iterable):
            callback(mutant, http_response)


class UrlOpenerProxy(object):
    """
    Proxy class for urlopener objects such as ExtendedUrllib instances.
    """

    def __init__(self, url_opener, plugin_inst):
        self._url_opener = url_opener
        self._plugin_inst = plugin_inst

    def __getattr__(self, name):
        def meth(*args, **kwargs):
            try:
                return attr(*args, **kwargs)
            except ScanMustStopOnUrlError, w3aferr:
                stopbubbling, result = \
                    self._plugin_inst.handle_url_error(w3aferr)
                if not stopbubbling:
                    try:
                        exc_info = sys.exc_info()
                        raise exc_info[0], exc_info[1], exc_info[2]
                    finally:
                        del exc_info
                return result
        attr = getattr(self._url_opener, name)
        return meth if callable(attr) else attr
