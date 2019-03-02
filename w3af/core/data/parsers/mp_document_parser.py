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
import psutil
import signal
import atexit
import resource
import threading
import multiprocessing

from concurrent.futures import TimeoutError
from tblib.decorators import Error
from pebble import ProcessPool
from pebble.common import ProcessExpired

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.profiling import start_profiling_no_core
from w3af.core.controllers.threads.is_main_process import is_main_process
from w3af.core.controllers.output_manager import log_sink_factory
from w3af.core.controllers.exceptions import ScanMustStopException
from w3af.core.controllers.ci.detect import is_running_on_ci
from w3af.core.controllers.threads.decorators import apply_with_return_error
from w3af.core.controllers.profiling.core_stats import core_profiling_is_enabled
from w3af.core.controllers.profiling.memory_usage import user_wants_memory_profiling
from w3af.core.controllers.profiling.pytracemalloc import user_wants_pytracemalloc
from w3af.core.controllers.profiling.cpu_usage import user_wants_cpu_profiling
from w3af.core.data.parsers.document_parser import DocumentParser
from w3af.core.data.parsers.ipc.serialization import (write_object_to_temp_file,
                                                      write_http_response_to_temp_file,
                                                      write_tags_to_temp_file,
                                                      load_object_from_temp_file,
                                                      load_http_response_from_temp_file,
                                                      load_tags_from_temp_file,
                                                      remove_file_if_exists)

# 128 MB
DEFAULT_MEMORY_LIMIT = 128 * 1024 * 1024


def get_memory_limit():
    env_memory_limit = os.environ.get('PARSER_MEMORY_LIMIT', '')

    if env_memory_limit.isdigit():
        msg = 'Using parser process virtual memory limit of %s bytes that was defined in env.'
        print(msg % env_memory_limit)
        return int(env_memory_limit)

    return DEFAULT_MEMORY_LIMIT


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

    # Document parsers can go crazy on memory usage when parsing some very
    # specific HTML / PDF documents. Sometimes when this happens the operating
    # system does an out of memory (OOM) kill of a "randomly chosen" process.
    #
    # We limit the memory which can be used by parsing processes to this constant
    #
    # The feature was tested in test_pebble_limit_memory_usage.py
    MEMORY_LIMIT = get_memory_limit()

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
                                         initargs=(log_queue, self.MEMORY_LIMIT))

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

        filename = write_http_response_to_temp_file(http_response)

        apply_args = (process_document_parser,
                      filename,
                      self.DEBUG)

        # Push the task to the workers
        try:
            future = self._pool.schedule(apply_with_return_error,
                                         args=(apply_args,),
                                         timeout=self.PARSER_TIMEOUT)
        except RuntimeError, rte:
            # Remove the temp file used to send data to the process
            remove_file_if_exists(filename)

            # We get here when the pebble pool management thread dies and
            # suddenly starts answering all calls with:
            #
            # RuntimeError('Unexpected error within the Pool')
            #
            # The scan needs to stop because we can't parse any more
            # HTTP responses, which is a very critical part of the process
            msg = str(rte)
            raise ScanMustStopException(msg)

        try:
            process_result = future.result()
        except TimeoutError:
            msg = ('[timeout] The parser took more than %s seconds'
                   ' to complete parsing of "%s", killed it!')
            args = (self.PARSER_TIMEOUT, http_response.get_url())
            raise TimeoutError(msg % args)
        except ProcessExpired:
            # We reach here when the process died because of an error, we
            # handle this just like when the parser takes a lot of time and
            # we're unable to retrieve an answer from it
            msg = ('One of the parser processes died unexpectedly, this could'
                   ' be because of a bug, the operating system triggering OOM'
                   ' kills, etc. The scanner will continue with the next'
                   ' document, but the scan results might be inconsistent.')
            raise TimeoutError(msg)
        finally:
            # Remove the temp file used to send data to the process, we already
            # have the result, so this file is not needed anymore
            remove_file_if_exists(filename)

        # We still need to perform some error handling here...
        if isinstance(process_result, Error):
            if isinstance(process_result.exc_value, MemoryError):
                msg = ('The parser exceeded the memory usage limit of %s bytes'
                       ' while trying to parse "%s". The parser was stopped in'
                       ' order to prevent OOM issues.')
                args = (self.MEMORY_LIMIT, http_response.get_url())
                om.out.debug(msg % args)
                raise MemoryError(msg % args)

            process_result.reraise()

        try:
            parser_output = load_object_from_temp_file(process_result)
        except Exception, e:
            msg = 'Failed to deserialize sub-process result. Exception: "%s"'
            args = (e,)
            raise Exception(msg % args)
        finally:
            remove_file_if_exists(process_result)

        # Success!
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

        filename = write_http_response_to_temp_file(http_response)

        apply_args = (process_get_tags_by_filter,
                      filename,
                      tags,
                      yield_text,
                      self.DEBUG)

        #
        # Push the task to the workers
        #
        try:
            future = self._pool.schedule(apply_with_return_error,
                                         args=(apply_args,),
                                         timeout=self.PARSER_TIMEOUT)
        except RuntimeError, rte:
            # Remove the temp file used to send data to the process
            remove_file_if_exists(filename)

            # We get here when the pebble pool management thread dies and
            # suddenly starts answering all calls with:
            #
            # RuntimeError('Unexpected error within the Pool')
            #
            # The scan needs to stop because we can't parse any more
            # HTTP responses, which is a very critical part of the process
            msg = str(rte)
            raise ScanMustStopException(msg)

        try:
            process_result = future.result()
        except TimeoutError:
            # We hit a timeout, return an empty list
            return []
        except ProcessExpired:
            # We reach here when the process died because of an error
            return []
        finally:
            # Remove the temp file used to send data to the process
            remove_file_if_exists(filename)

        # There was an exception in the parser, maybe the HTML was really
        # broken, or it wasn't an HTML at all.
        if isinstance(process_result, Error):
            if isinstance(process_result.exc_value, MemoryError):
                msg = ('The parser exceeded the memory usage limit of %s bytes'
                       ' while trying to parse "%s". The parser was stopped in'
                       ' order to prevent OOM issues.')
                args = (self.MEMORY_LIMIT, http_response.get_url())
                om.out.debug(msg % args)

            return []

        try:
            filtered_tags = load_tags_from_temp_file(process_result)
        except Exception, e:
            msg = 'Failed to deserialize sub-process result. Exception: "%s"'
            args = (e,)
            raise Exception(msg % args)
        finally:
            remove_file_if_exists(process_result)

        return filtered_tags


def process_get_tags_by_filter(filename, tags, yield_text, debug):
    """
    Simple wrapper to get the current process id and store it in a shared object
    so we can kill the process if needed.
    """
    http_resp = load_http_response_from_temp_file(filename)

    document_parser = DocumentParser(http_resp)
    parser = document_parser.get_parser()

    # Not all parsers have tags
    if not hasattr(parser, 'get_tags_by_filter'):
        return write_tags_to_temp_file([])

    filtered_tags = []
    for tag in parser.get_tags_by_filter(tags, yield_text=yield_text):
        filtered_tags.append(tag)

    msg = ('Returned %s Tag instances at get_tags_by_filter() for URL %s'
           ' and tags filter %r')
    args = (len(filtered_tags), http_resp.get_uri(), tags)
    om.out.debug(msg % args)

    result_filename = write_tags_to_temp_file(filtered_tags)

    return result_filename


def process_document_parser(filename, debug):
    """
    Simple wrapper to get the current process id and store it in a shared object
    so we can kill the process if needed.
    """
    http_resp = load_http_response_from_temp_file(filename)
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

    result_filename = write_object_to_temp_file(document_parser)

    return result_filename


@atexit.register
def cleanup_pool():
    if 'mp_doc_parser' in globals():
        mp_doc_parser.stop_workers()


def init_worker(log_queue, mem_limit):
    """
    This function is called right after each Process in the ProcessPool is
    created, and it will initialized some variables/handlers which are required
    for it to work as expected

    :return: None
    """
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    log_sink_factory(log_queue)
    start_profiling_no_core()
    limit_memory_usage(mem_limit)


def limit_memory_usage(mem_limit):
    """
    Set the soft memory limit for the worker process.

    Retrieve current limits, re-use the hard limit.

    See documentation on resources at:
        https://linux.die.net/man/2/getrlimit

    Not available:
        RLIMIT_RSS is not available for new kernel versions

    Could work:
        RLIMIT_AS The maximum size of the process's virtual memory
                  (address space) in bytes.

                  Reminder of how virtual memory works:
                  https://en.wikipedia.org/wiki/Virtual_memory

        RLIMIT_STACK The maximum size of the process stack, in bytes.
        RLIMIT_DATA The maximum size of the process's data segment
                    (initialized data, uninitialized data, and heap)

    Not sure:
        RLIMIT_MEMLOCK The maximum number of bytes of memory that may
        be locked into RAM
    """
    # This works on Linux only (for now)
    if not hasattr(resource, 'RLIMIT_AS'):
        print('w3af was unable to limit the memory usage of parser processes.'
              ' This feature is only supported in Linux OS, create an issue'
              ' in our repository and we might implement it for your OS.')
        return

    # Note that this is run on every process start, which is what we need
    #
    # Since the real memory limit will be w3af's main process memory usage
    # plus the imposed memory limit (mem_limit) we want to calculate this
    # as often as possible.
    #
    # New processes are created in the pool after 20 jobs (max_tasks=20) so
    # that should take care of cycling processes with different real memory
    # limits
    try:
        p = psutil.Process()
    except (psutil.NoSuchProcess, psutil.ZombieProcess) as e:
        error = ('Failed to limit parser process memory usage: "%s". The scan'
                 ' will continue but in some scenarios the HTTP response'
                 ' parsers might use a large amount of memory.')
        om.out.error(error % e)
        return

    real_memory_limit = p.memory_info().vms + mem_limit

    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    resource.setrlimit(resource.RLIMIT_AS, (real_memory_limit, hard))

    limit_mb = (real_memory_limit / 1024 / 1024)
    msg = 'Using RLIMIT_AS memory usage limit %s MB for new pool process'
    om.out.debug(msg % limit_mb)


if is_main_process():
    mp_doc_parser = MultiProcessingDocumentParser()
