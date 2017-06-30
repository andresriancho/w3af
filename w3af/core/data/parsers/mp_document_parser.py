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

import signal
import atexit
import threading
import multiprocessing

from concurrent.futures import TimeoutError
from tblib.decorators import Error
from pebble import ProcessPool

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.profiling import start_profiling_no_core
from w3af.core.controllers.threads.is_main_process import is_main_process
from w3af.core.controllers.output_manager import log_sink_factory
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.ci.detect import is_running_on_ci
from w3af.core.controllers.threads.decorators import apply_with_return_error
from w3af.core.controllers.profiling.core_stats import core_profiling_is_enabled
from w3af.core.controllers.profiling.memory_usage import user_wants_memory_profiling
from w3af.core.controllers.profiling.pytracemalloc import user_wants_pytracemalloc
from w3af.core.controllers.profiling.cpu_usage import user_wants_cpu_profiling
from w3af.core.data.parsers.document_parser import DocumentParser


class MultiProcessingDocumentParser(object):
    """
    A document parser that performs all it's tasks in different processes and
    returns results to the main process.

    Also implements a parsing timeout just in case the parser enters an infinite
    loop.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    DEBUG = core_profiling_is_enabled()
    MAX_WORKERS = 2 if is_running_on_ci() else (multiprocessing.cpu_count() / 2) or 1

    # Increasing the timeout when profiling is enabled seems to fix issue #9713
    #
    # https://github.com/andresriancho/w3af/issues/9713
    PROFILING_ENABLED = (user_wants_memory_profiling() or
                         user_wants_pytracemalloc() or
                         user_wants_cpu_profiling())

    # in seconds
    PARSER_TIMEOUT = 60 * 3 if PROFILING_ENABLED else 10

    def __init__(self):
        self._pool = None
        self._start_lock = threading.RLock()

    def start_workers(self):
        """
        Start the pool and workers
        :return: The pool instance
        """
        with self._start_lock:
            if self._pool is None:

                # Start the process pool
                log_queue = om.manager.get_in_queue()
                self._pool = ProcessPool(self.MAX_WORKERS,
                                         max_tasks=20,
                                         initializer=init_worker,
                                         initargs=(log_queue,))

        return self._pool

    def stop_workers(self):
        """
        Stop the pool workers
        :return: None
        """
        if self._pool is not None:
            self._pool.stop()
            self._pool.join()
            self._pool = None

    def get_document_parser_for(self, http_response):
        """
        Get a document parser for http_response

        This parses the http_response in a pool worker. This method has two
        features:
            * We can kill the worker if the parser is taking too long
            * We can have different parsers

        :param http_response: The http response instance
        :return: An instance of DocumentParser
        """
        # Start the worker processes if needed
        self.start_workers()

        apply_args = (process_document_parser,
                      http_response,
                      self.DEBUG)

        # Push the task to the workers
        future = self._pool.schedule(apply_with_return_error,
                                     args=(apply_args,),
                                     timeout=self.PARSER_TIMEOUT)

        try:
            parser_output = future.result()
        except TimeoutError:
            # Act just like when there is no parser
            msg = ('[timeout] The parser took more than %s seconds'
                   ' to complete parsing of "%s", killed it!')

            args = (self.PARSER_TIMEOUT, http_response.get_url())

            raise BaseFrameworkException(msg % args)
        else:
            if isinstance(parser_output, Error):
                parser_output.reraise()

        return parser_output

    def get_tags_by_filter(self, http_response, tags, yield_text=False):
        """
        Return Tag instances for the tags which match the `tags` filter,
        parsing and all lxml stuff is done in another process and the Tag
        instances are sent to the main process (the one calling this method)
        through a pipe

        Some things to note:
            * Not all responses can be parsed, so I need to call DocumentParser
              and handle exceptions

            * The parser selected by DocumentParser might not have tags, and
              it might not have get_tags_by_filter. In this case just return an
              empty list

            * Just like get_document_parser_for we have a timeout in place,
              when we hit the timeout just return an empty list, this is not
              the best thing to do, but makes the plugin code easier to write
              (plugins would ignore this anyways)

        :param tags: The filter
        :param yield_text: Should we yield the tag text?
        :return: A list of Tag instances as defined in sgml.py

        :see: SGMLParser.get_tags_by_filter
        """
        # Start the worker processes if needed
        self.start_workers()

        apply_args = (process_get_tags_by_filter,
                      http_response,
                      tags,
                      yield_text,
                      self.DEBUG)

        # Push the task to the workers
        future = self._pool.schedule(apply_with_return_error,
                                     args=(apply_args,),
                                     timeout=self.PARSER_TIMEOUT)

        try:
            filtered_tags = future.result()
        except TimeoutError:
            # We hit a timeout, return an empty list
            return []
        else:
            # There was an exception in the parser, maybe the HTML was really
            # broken, or it wasn't an HTML at all.
            if isinstance(filtered_tags, Error):
                return []

        return filtered_tags


def process_get_tags_by_filter(http_resp, tags, yield_text, debug):
    """
    Simple wrapper to get the current process id and store it in a shared object
    so we can kill the process if needed.
    """
    document_parser = DocumentParser(http_resp)

    # Not all parsers have tags
    if not hasattr(document_parser, 'get_tags_by_filter'):
        return []

    filtered_tags = []
    for tag in document_parser.get_tags_by_filter(tags, yield_text=yield_text):
        filtered_tags.append(tag)

    return filtered_tags


def process_document_parser(http_resp, debug):
    """
    Simple wrapper to get the current process id and store it in a shared object
    so we can kill the process if needed.
    """
    pid = multiprocessing.current_process().pid

    if debug:
        msg = '[mp_document_parser] PID %s is starting to parse %s'
        args = (pid, http_resp.get_url())
        om.out.debug(msg % args)

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


if is_main_process():
    mp_doc_parser = MultiProcessingDocumentParser()
