"""
mp_document_parser.py

Copyright 2015 Andres Riancho

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
import signal
import atexit
import threading
import multiprocessing

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
from w3af.core.data.parsers.utils.request_uniq_id import get_request_unique_id


class MultiProcessingDocumentParser(object):
    """
    A document parser that performs all it's tasks in different processes and
    returns results to the main process.

    Also implements a parsing timeout just in case the parser enters an infinite
    loop.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    # in seconds
    PARSER_TIMEOUT = 10
    DEBUG = core_profiling_is_enabled()
    MAX_WORKERS = 2 if is_running_on_ci() else (multiprocessing.cpu_count() / 2) or 1

    def __init__(self):
        self._pool = None
        self._processes = None
        self._start_lock = threading.RLock()

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
                                         maxtasksperchild=20,
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

            self._processes.clear()
            self._processes = None

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

    def _parse_http_response_in_worker(self, http_response, hash_string):
        """
        This parses the http_response in a pool worker. This has two features:
            * We can kill the worker if the parser is taking too long
            * We can have different parsers

        :return: The DocumentParser instance
        """
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

            # Act just like when there is no parser
            msg = 'There is no parser for "%s".' % http_response.get_url()
            raise BaseFrameworkException(msg)
        else:
            if isinstance(parser_output, Error):
                parser_output.reraise()

        finally:
            # Just remove it so it doesn't use memory
            self._processes.pop(hash_string, None)

        return parser_output

    def get_document_parser_for(self, http_response):
        """
        Get a document parser for http_response

        :param http_response: The http response instance
        :return: An instance of DocumentParser
        """
        hash_string = get_request_unique_id(http_response)
        return self._parse_http_response_in_worker(http_response, hash_string)


def process_document_parser(http_resp, processes, hash_string, debug):
    """
    Simple wrapper to get the current process id and store it in a shared object
    so we can kill the process if needed.
    """
    pid = multiprocessing.current_process().pid

    if debug:
        msg = '[mp_document_parser] PID %s is starting to parse %s'
        args = (pid, http_resp.get_url())
        om.out.debug(msg % args)

    # Save this for tracking
    processes[hash_string] = pid

    try:
        # Parse
        document_parser = DocumentParser(http_resp)
    except Exception, e:
        if debug:
            msg = ('[mp_document_parser] PID %s finished parsing %s with'
                   ' exception: "%s"')
            args = (pid, http_resp.get_url(), e)
            om.out.debug(msg % args)
        raise
    else:
        if debug:
            msg = ('[mp_document_parser] PID %s finished parsing %s without any'
                   ' exception')
            args = (pid, http_resp.get_url())
            om.out.debug(msg % args)

    return document_parser


@atexit.register
def cleanup_pool():
    if 'mp_doc_parser' in globals():
        mp_doc_parser.stop_workers()

    # to be safe -- explicitly shutting down the manager
    if 'manager' in globals():
        manager.shutdown()


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
    mp_doc_parser = MultiProcessingDocumentParser()
