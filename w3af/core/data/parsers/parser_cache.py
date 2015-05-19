"""
parser_cache.py

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
from __future__ import with_statement, print_function

import os
import zlib
import signal
import atexit
import threading
import multiprocessing

from multiprocessing.managers import SyncManager, State
from darts.lib.utils.lru import SynchronizedLRUDict
from tblib.decorators import Error

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.profiling import start_profiling_no_core
from w3af.core.controllers.threads.process_pool import ProcessPool
from w3af.core.controllers.threads.is_main_process import is_main_process
from w3af.core.controllers.output_manager import log_sink_factory
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.ci.detect import is_running_on_ci
from w3af.core.controllers.threads.decorators import apply_with_return_error
from w3af.core.controllers.profiling.core_stats import core_profiling_is_enabled
from w3af.core.controllers.profiling.memory_usage import user_wants_memory_profiling
from w3af.core.controllers.profiling.pytracemalloc import user_wants_pytracemalloc
from w3af.core.data.parsers.document_parser import DocumentParser


class ParserCache(object):
    """
    This class is a document parser cache.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    CACHE_SIZE = 10
    MAX_CACHEABLE_BODY_LEN = 1024 * 1024
    DEBUG = core_profiling_is_enabled()
    MAX_WORKERS = 2 if is_running_on_ci() else (multiprocessing.cpu_count() / 2) or 1
    # in seconds
    PARSER_TIMEOUT = 60

    def __init__(self):
        self._cache = SynchronizedLRUDict(self.CACHE_SIZE)
        self._pool = None
        self._processes = None
        self._parser_finished_events = {}
        self._start_lock = threading.RLock()

        # These are here for debugging:
        self._from_LRU = 0.0
        self._do_not_cache = 0.0
        self._total = 0.0

    def start_workers(self):
        """
        Start the pool and workers
        :return: The pool instance
        """
        with self._start_lock:
            if self._pool is None:

                # pylint: disable=E1101
                # Keep track of which pid is processing which http response
                self._processes = manager.dict()
                # pylint: enable=E1101

                # The pool
                log_queue = om.manager.get_in_queue()
                self._pool = ProcessPool(self.MAX_WORKERS,
                                         maxtasksperchild=25,
                                         initializer=init_worker,
                                         initargs=(log_queue,))

        return self._pool

    def stop_workers(self):
        """
        Stop the pool workers
        :return: None
        """
        if self._pool is not None:
            self._pool.terminate()
            self._pool = None
            self._processes = None

        # Make sure the parsers clear all resources
        for parser in self._cache.itervalues():
            parser.clear()

        # We don't need the parsers anymore
        self._cache.clear()

    def shutdown(self):
        self.stop_workers()

        # to be safe -- explicitly shutting down the manager
        manager.shutdown()

    def get_hit_rate(self):
        """
        :note: Only returns useful information if debugging is enabled
        """
        try:
            return self._from_LRU / self._total
        except ZeroDivisionError:
            return None

    def get_max_lru_items(self):
        """
        :note: Only returns useful information if debugging is enabled
        """
        return self.CACHE_SIZE

    def get_current_lru_items(self):
        """
        :note: Only returns useful information if debugging is enabled
        """
        return len(self._cache)

    def get_total_queries(self):
        return self._total

    def get_do_not_cache(self):
        return self._do_not_cache

    def get_cache_key(self, http_response):
        """
        Before I used md5, but I realized that it was unnecessary. I
        experimented a little bit with python's hash functions and the builtin
        hash was the fastest.

        At first I thought that the built-in hash wasn't good enough, as it
        could create collisions... but... given that the LRU has only 40
        positions, the real probability of a collision is too low.

        :return: The key to be used in the cache for storing this http_response
        """
        # @see: test_bug_13_Dec_2012 to understand why we concat the uri to the
        #       body before hashing
        uri_str = http_response.get_uri().url_string.encode('utf-8')

        body_str = http_response.body
        if isinstance(body_str, unicode):
            body_str = body_str.encode('utf-8', 'replace')

        _to_hash = body_str + uri_str

        # Added adler32 after finding some hash() collisions in builds
        hash_string = str(hash(_to_hash))
        hash_string += str(zlib.adler32(_to_hash))
        return hash_string

    def should_cache(self, http_response):
        """
        Defines if this http_response parser should be cached or not

        :param http_response: The http response instance
        :return: True if we should cache the parser for this response
        """
        return len(http_response.get_body()) < self.MAX_CACHEABLE_BODY_LEN

    def _test_parse_http_response(self, http_response, *args):
        """
        Left here for testing!
        """
        return DocumentParser(http_response)

    def _kill_parser_process(self, hash_string, http_response):
        """
        Kill the process that's handling the parsing of http_response which
        can be identified by hash_string

        :param hash_string: The hash for the http_response
        :param http_response: The HTTP response which is being parsed
        :return: None
        """
        # Near the timeout error, so we make sure that the pid is still
        # running our "buggy" input
        pid = self._processes.pop(hash_string, None)
        if pid is not None:
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError, ose:
                msg = ('An error occurred while killing the parser'
                       ' process: "%s"')
                om.out.debug(msg % ose)

        msg = ('[timeout] The parser took more than %s seconds to complete'
               ' parsing of "%s", killed it!')

        if user_wants_memory_profiling() or user_wants_pytracemalloc():
            msg += (' Keep in mind that you\'re profiling memory usage and'
                    ' there is a known bug where memory profilers break the'
                    ' parser cache. See issue #9713 for more information'
                    ' https://github.com/andresriancho/w3af/issues/9713')

        om.out.debug(msg % (self.PARSER_TIMEOUT, http_response.get_url()))

    def _spawn_new_parser_process(self):
        """
        The process pool doesn't know how to handle the fact that one of the
        workers was abruptly killed, so we help the Pool recover

        :see: https://github.com/andresriancho/w3af/issues/9713
        :return: None
        """
        pass

    def _parse_http_response_in_worker(self, http_response, hash_string):
        """
        This parses the http_response in a pool worker. This has two features:
            * We can kill the worker if the parser is taking too long
            * We can have different parsers

        :return: The DocumentParser instance
        """
        event = multiprocessing.Event()
        self._parser_finished_events[hash_string] = event

        # Start the worker processes if needed
        self.start_workers()

        apply_args = (process_document_parser,
                      http_response,
                      self._processes,
                      hash_string,
                      self.DEBUG)

        # Push the task to the workers
        result = self._pool.apply_async(apply_with_return_error, (apply_args,))

        try:
            parser_output = result.get(timeout=self.PARSER_TIMEOUT)
        except multiprocessing.TimeoutError:
            self._kill_parser_process(hash_string, http_response)
            self._spawn_new_parser_process()

            # Act just like when there is no parser
            msg = 'There is no parser for "%s".' % http_response.get_url()
            raise BaseFrameworkException(msg)
        else:
            if isinstance(parser_output, Error):
                parser_output.reraise()

        finally:
            # Just remove it so it doesn't use memory
            self._processes.pop(hash_string, None)

            # Let other threads know that we're done
            event = self._parser_finished_events.pop(hash_string, None)

            if event is not None:
                # There is a really rare race condition where more than one
                # thread calls _parse_http_response_in_worker and queues the
                # same hash_string for processing, since it's so rare I believe
                # the best way to fix it is to:
                #
                #   * Avoid adding a lock
                #   * Accept that in these rare edge case we'll waste some CPU
                #
                # https://circleci.com/gh/andresriancho/w3af/1354
                event.set()

        return parser_output

    def get_document_parser_for(self, http_response, cache=True):
        """
        Get a document parser for http_response using the cache if required

        :param http_response: The http response instance
        :return: An instance of DocumentParser
        """
        hash_string = self.get_cache_key(http_response)

        parser_finished = self._parser_finished_events.get(hash_string, None)
        if parser_finished is not None:
            # There is one subprocess already processing this http response
            # body, the best thing to do here is to make this thread wait
            # until that process has finished
            try:
                parser_finished.wait(timeout=self.PARSER_TIMEOUT)
            except:
                # Act just like when there is no parser
                msg = 'There is no parser for "%s".' % http_response.get_url()
                raise BaseFrameworkException(msg)

        # metric increase
        self._total += 1

        if not self.should_cache(http_response) or not cache:
            # Just return the document parser, no need to cache
            self._debug_handle_no_cache(hash_string)
            return self._parse_http_response_in_worker(http_response,
                                                       hash_string)

        parser = self._cache.get(hash_string, None)
        if parser is not None:
            self._debug_handle_cache_hit(hash_string)
            return parser
        else:
            self._debug_handle_cache_miss(hash_string)

            # Create a new instance of DocumentParser, add it to the cache
            parser = self._parse_http_response_in_worker(http_response,
                                                         hash_string)
            self._cache[hash_string] = parser
            return parser

    def _debug_handle_cache_hit(self, hash_string):
        if self.DEBUG:
            om.out.debug('[parser_cache] Hit for %s' % hash_string)
            self._from_LRU += 1

    def _debug_handle_cache_miss(self, hash_string):
        if self.DEBUG:
            om.out.debug('[parser_cache] Miss for %s' % hash_string)

    def _debug_handle_no_cache(self, hash_string):
        if self.DEBUG:
            om.out.debug('[parser_cache] DO NOT CACHE %s' % hash_string)
            self._do_not_cache += 1


def process_document_parser(http_resp, processes, hash_string, debug):
    """
    Simple wrapper to get the current process id and store it in a shared object
    so we can kill the process if needed.
    """
    pid = multiprocessing.current_process().pid

    if debug:
        msg = '[parser_cache] PID %s is starting to parse %s'
        args = (pid, http_resp.get_url())
        om.out.debug(msg % args)

    # Save this for tracking
    processes[hash_string] = pid

    try:
        # Parse
        document_parser = DocumentParser(http_resp)
    except Exception, e:
        if debug:
            msg = ('[parser_cache] PID %s finished parsing %s with'
                   ' exception: "%s"')
            args = (pid, http_resp.get_url(), e)
            om.out.debug(msg % args)
        raise
    else:
        if debug:
            msg = ('[parser_cache] PID %s finished parsing %s without any'
                   ' exception')
            args = (pid, http_resp.get_url())
            om.out.debug(msg % args)

    return document_parser


@atexit.register
def cleanup_pool():
    if 'dpc' in globals():
        dpc.stop_workers()
    

def init_worker(log_queue):
    """
    This function is called right after each Process in the ProcessPool is
    created, and it will initialized some variables/handlers which are required
    for it to work as expected

    :return: None
    """
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    log_sink_factory(log_queue)
    start_profiling_no_core()


def init_manager():
    """
    Initializer for SyncManager
    :see: https://jtushman.github.io/blog/2014/01/14/python-%7C-multiprocessing-and-interrupts/
    """
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def Manager():
    """
    Returns a manager associated with a running server process

    The managers methods such as `Lock()`, `Condition()` and `Queue()`
    can be used to create shared objects.
    """
    from multiprocessing.managers import SyncManager
    m = SyncManager()
    m.start(init_manager)
    return m


if is_main_process():
    manager = Manager()
    dpc = ParserCache()
