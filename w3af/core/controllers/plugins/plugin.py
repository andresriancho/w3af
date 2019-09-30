"""
plugin.py

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
import Queue
import threading

from itertools import repeat
from tblib.decorators import Error

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.configurable import Configurable
from w3af.core.controllers.threads.threadpool import return_args
from w3af.core.controllers.exceptions import HTTPRequestException
from w3af.core.controllers.threads.decorators import apply_with_return_error
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.url.helpers import new_no_content_resp
from w3af.core.data.kb.info_set import InfoSet


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
        Create some generic attributes that are going to be used by most plugins
        """
        self._uri_opener = None
        self._w3af_core = None
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

    def set_url_opener(self, url_opener):
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
        self._uri_opener = UrlOpenerProxy(url_opener, self)

    def set_w3af_core(self, w3af_core):
        """
        Set the w3af core instance to the plugin. This shouldn't be used much
        but it is helpful when the plugin needs to query something about the
        core status.

        :return: None
        """
        self._w3af_core = w3af_core

    def get_w3af_core(self):
        return self._w3af_core

    def set_options(self, options_list):
        """
        Sets the Options given on the OptionList to self. The options are the
        result of a user entering some data on a window that was constructed
        using the options that were retrieved from the plugin using
        get_options()

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
        msg = 'Plugin is not implementing required method get_long_desc'
        raise NotImplementedError(msg)

    def kb_append_uniq(self, location_a, location_b, info, filter_by='VAR'):
        """
        kb.kb.append_uniq a vulnerability to the KB
        """
        added_to_kb = kb.kb.append_uniq(location_a,
                                        location_b,
                                        info,
                                        filter_by=filter_by)

        if added_to_kb:
            om.out.report_finding(info)

        return added_to_kb

    def kb_append_uniq_group(self, location_a, location_b, info,
                             group_klass=InfoSet):
        """
        kb.kb.append_uniq_group a vulnerability to the KB
        """
        info_set, created = kb.kb.append_uniq_group(location_a,
                                                    location_b,
                                                    info,
                                                    group_klass=group_klass)

        if created:
            om.out.report_finding(info_set.first_info)

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

    def __repr__(self):
        return '<%s.%s>' % (self.get_type(), self.get_name())

    def end(self):
        """
        This method is called by w3afCore to let the plugin know that it wont
        be used anymore. This is helpful to do some final tests, free some
        structures, etc.
        """
        pass

    def get_type(self):
        return 'plugin'

    def get_name(self):
        return self.__class__.__name__

    def _send_mutants_in_threads(self, func, iterable, callback, **kwds):
        """
        Please note that this method blocks from the caller's point of view
        but performs all the HTTP requests in parallel threads.

        :param func: The function to use to send the mutants
        :param iterable: A list with the mutants
        :param callback: A callable to invoke after each mutant is sent
        """
        imap_unordered = self.worker_pool.imap_unordered
        awre = apply_with_return_error

        try:
            num_tasks = len(iterable)
        except TypeError:
            # When the iterable is a python iterator which doesn't implement
            # the __len__, then we don't know the number of received tasks
            pass
        else:
            debugging_id = kwds.get('debugging_id', 'unknown')
            msg = 'send_mutants_in_threads will send %s HTTP requests (did:%s)'
            args = (num_tasks, debugging_id)
            om.out.debug(msg % args)

        # You can use this code to debug issues that happen in threads, by
        # simply not using them:
        #
        # for i in iterable:
        #    callback(i, func(i))
        # return
        #
        # Now the real code:
        func = return_args(func, **kwds)
        args = zip(repeat(func), iterable)

        for result in imap_unordered(awre, args):
            # re-raise the thread exception in the main thread with this method
            # so we get a nice traceback instead of things like the ones we see
            # in https://github.com/andresriancho/w3af/issues/7286
            if isinstance(result, Error):
                result.reraise()
            else:
                (mutant,), http_response = result
                callback(mutant, http_response)

    def handle_url_error(self, uri, http_exception):
        """
        Handle UrlError exceptions raised when requests are made.
        Subclasses should redefine this method for a more refined
        behavior and must respect the return value format.

        :param http_exception: HTTPRequestException exception instance

        :return: A tuple containing:
            * re_raise: Boolean value that indicates the caller if the original
                        exception should be re-raised after this error handling
                        method.

            * result: The result to be returned to the caller. This only makes
                      sense if re_raise is False.
        """
        no_content_resp = new_no_content_resp(uri, add_id=True)
        
        msg = ('The %s plugin got an error while requesting "%s".'
               ' Exception: "%s".'
               ' Generated 204 "No Content" response (id:%s)')
        args = (self.get_name(),
                uri,
                http_exception,
                no_content_resp.id)
        om.out.error(msg % args)

        return False, no_content_resp


class UrlOpenerProxy(object):
    """
    Proxy class for urlopener objects such as ExtendedUrllib instances.
    """
    # I want to list all the methods which I do NOT want to wrap, I have to
    # do it this way since the extended_urllib.py also implements __getattr__
    # to provide PUT, PATCH, etc. methods.
    #
    # These methods won't be wrapped, mostly because they either:
    #   * Don't return an HTTPResponse
    #   * Don't raise HTTPRequestException
    #
    # I noticed this issue when #8705 was reported
    # https://github.com/andresriancho/w3af/issues/8705
    NO_WRAPPER_FOR = {'send_clean',
                      'clear',
                      'end',
                      'restart',
                      'get_headers',
                      'get_cookies',
                      'get_remote_file_size',
                      'add_headers',
                      'assert_allowed_proto',
                      'get_average_rtt_for_mutant',
                      '_handle_send_socket_error',
                      '_handle_send_urllib_error',
                      '_handle_send_success',
                      '_handle_error_on_increment'
                      '_generic_send_error_handler',
                      '_increment_global_error_count',
                      '_log_successful_response'}

    def __init__(self, url_opener, plugin_inst):
        self._url_opener = url_opener
        self._plugin_inst = plugin_inst

    def __getattr__(self, name):

        attr = getattr(self._url_opener, name)

        def url_opener_proxy(*args, **kwargs):
            try:
                return attr(*args, **kwargs)
            except HTTPRequestException, hre:
                #
                # We get here when **one** HTTP request fails. When more than
                # one exception fails the URL opener will raise a different
                # type of exception (not a subclass of HTTPRequestException)
                # and that one will bubble up to w3afCore/strategy/etc.
                #
                arg1 = args[0]
                if hasattr(arg1, 'get_uri'):
                    # Mutants and fuzzable requests enter here
                    uri = arg1.get_uri()
                else:
                    # It was a URL instance
                    uri = arg1

                re_raise, result = self._plugin_inst.handle_url_error(uri, hre)

                # By default we do NOT re-raise, we just return a 204-no content
                # response and hope for the best.
                if re_raise:
                    exc_info = sys.exc_info()
                    raise exc_info[0], exc_info[1], exc_info[2]

                return result

        if name in self.NO_WRAPPER_FOR:
            # See note above on NO_WRAPPER_FOR
            return attr
        elif callable(attr):
            return url_opener_proxy
        else:
            return attr
