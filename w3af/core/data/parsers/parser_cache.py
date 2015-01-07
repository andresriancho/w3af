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
import signal
import multiprocessing

from darts.lib.utils.lru import LRUDict
from tblib.decorators import apply_with_return_error, Error

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.output_manager import log_sink_factory
from w3af.core.data.parsers.document_parser import DocumentParser
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.ci.detect import is_running_on_ci


class ParserCache(object):
    """
    This class is a document parser cache.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    LRU_LENGTH = 40
    MAX_CACHEABLE_BODY_LEN = 1024 * 1024
    PARSER_TIMEOUT = 60 # in seconds
    DEBUG = False
    MAX_WORKERS = 2 if is_running_on_ci() else (multiprocessing.cpu_count() / 2) or 1

    def __init__(self):
        self._cache = LRUDict(self.LRU_LENGTH)
        self._pool = None
        self._processes = None
        self._parser_finished_events = {}

        # These are here for debugging:
        self._archive = set()
        self._from_LRU = 0.0
        self._calculated_more_than_once = 0.0
        self._total = 0.0

    def start_workers(self):
        """
        Start the pool and workers
        :return: The pool instance
        """
        if self._pool is None:
            # Keep track of which pid is processing which http response
            self._processes = manager.dict()

            # The pool
            log_queue = om.manager.get_in_queue()
            self._pool = multiprocessing.Pool(self.MAX_WORKERS,
                                              maxtasksperchild=25,
                                              initializer=log_sink_factory,
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

        if self.DEBUG:
            print('parser_cache LRU rate: %s' % (self._from_LRU / self._total))
            print('parser_cache re-calculation rate: %s' % (self._calculated_more_than_once / self._total))
            print('parser_cache size: %s' % self.LRU_LENGTH)

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

        hash_string = hash(body_str + uri_str)
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

    def _parse_http_response_in_worker(self, http_response, hash_string):
        """
        This parses the http_response in a pool worker. This has two features:
            * We can kill the worker if the parser is taking too long
            * We can have different parsers

        :return: The DocumentParser instance
        """
        event = multiprocessing.Event()
        self._parser_finished_events[hash_string] = event

        apply_args = (ProcessDocumentParser,
                      http_response,
                      self._processes,
                      hash_string)

        result = self._pool.apply_async(apply_with_return_error, (apply_args,))

        try:
            parser_output = result.get(timeout=self.PARSER_TIMEOUT)
        except multiprocessing.TimeoutError:
            # Near the timeout error, so we make sure that the pid is still
            # running our "buggy" input
            pid = self._processes[hash_string]
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError, ose:
                msg = 'An error occurred while killing the parser process: "%s"'
                om.out.debug(msg % ose)
            else:
                msg = '[timeout] The parser took more than %s seconds'\
                      ' to complete parsing of "%s", killed it!'

                om.out.debug(msg % (self.PARSER_TIMEOUT,
                                    http_response.get_url()))

            # Act just like when there is no parser
            msg = 'There is no parser for "%s".' % http_response.get_url()
            raise BaseFrameworkException(msg)
        else:
            if isinstance(parser_output, Error):
                parser_output.reraise()

        finally:
            # Just remove it so it doesn't use memory
            self._processes.pop(hash_string)

            # Let other know that we're done
            event = self._parser_finished_events.pop(hash_string)
            event.set()

        return parser_output

    def get_document_parser_for(self, http_response):
        """
        Get a document parser for http_response using the cache if required

        :param http_response: The http response instance
        :return: An instance of DocumentParser
        """
        self.start_workers()
        hash_string = self.get_cache_key(http_response)

        if not self.should_cache(http_response):
            # Just return the document parser, no need to cache
            return self._parse_http_response_in_worker(http_response,
                                                       hash_string)

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

        parser = self._cache.get(hash_string, None)
        if parser is not None:
            self._debug_in_cache(hash_string)
            return parser
        else:
            # Create a new instance of DocumentParser, add it to the cache
            parser = self._parse_http_response_in_worker(http_response,
                                                         hash_string)
            self._cache[hash_string] = parser
            self._debug_not_in_cache(hash_string)
            return parser

    def _debug_not_in_cache(self, hash_string):
        if self.DEBUG:
            self._total += 1

            if hash_string in self._archive:
                msg = '[%s] calculated and was in archive. (bad)'
                print(msg % hash_string)
                self._calculated_more_than_once += 1
            else:
                msg = '[%s] calculated for the first time and cached. (good)'
                print(msg % hash_string)
                self._archive.add(hash_string)

    def _debug_in_cache(self, hash_string):
        if self.DEBUG:
            self._total += 1

            if hash_string in self._archive:
                msg = '[%s] return from LRU and was in archive. (good)'
                print(msg % hash_string)
                self._from_LRU += 1


class ProcessDocumentParser(DocumentParser):
    """
    Simple wrapper to get the current process id and store it in a shared object
    so we can kill the process if needed.
    """
    def __init__(self, http_resp, processes, hash_string):
        pid = multiprocessing.current_process().pid
        processes[hash_string] = pid
        
        super(ProcessDocumentParser, self).__init__(http_resp)


manager = multiprocessing.Manager()
dpc = ParserCache()
