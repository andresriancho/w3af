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

import atexit
import threading

from darts.lib.utils.lru import SynchronizedLRUDict

from w3af.core.controllers.threads.is_main_process import is_main_process
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.profiling.core_stats import core_profiling_is_enabled
from w3af.core.data.parsers.utils.request_uniq_id import get_request_unique_id
from w3af.core.data.parsers.mp_document_parser import MultiProcessingDocumentParser
from w3af.core.data.parsers.utils.cache_stats import CacheStats


class ParserCache(CacheStats):
    """
    This class is a document parser cache.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    CACHE_SIZE = 10
    MAX_CACHEABLE_BODY_LEN = 1024 * 1024
    DEBUG = core_profiling_is_enabled()

    def __init__(self):
        super(ParserCache, self).__init__()
        
        self._cache = SynchronizedLRUDict(self.CACHE_SIZE)
        self._parser_finished_events = {}
        self._mp_doc_parser = MultiProcessingDocumentParser()

    def clear(self):
        """
        Clear all the internal variables
        :return: None
        """
        # Stop any workers
        self._mp_doc_parser.stop_workers()

        # Make sure the parsers clear all resources
        for parser in self._cache.itervalues():
            parser.clear()

        # We don't need the parsers anymore
        self._cache.clear()

    def should_cache(self, http_response):
        """
        Defines if this http_response parser should be cached or not

        :param http_response: The http response instance
        :return: True if we should cache the parser for this response
        """
        return len(http_response.get_body()) < self.MAX_CACHEABLE_BODY_LEN

    def get_document_parser_for(self, http_response, cache=True):
        """
        Get a document parser for http_response using the cache if required

        :param http_response: The http response instance
        :return: An instance of DocumentParser
        """
        hash_string = get_request_unique_id(http_response)

        parser_finished = self._parser_finished_events.get(hash_string, None)
        if parser_finished is not None:
            # There is one subprocess already processing this http response
            # body, the best thing to do here is to make this thread wait
            # until that process has finished
            timeout = MultiProcessingDocumentParser.PARSER_TIMEOUT
            try:
                parser_finished.wait(timeout=timeout)
            except:
                # Act just like when there is no parser
                msg = 'There is no parser for "%s". Waited more than %s sec.'
                args = (http_response.get_url(), timeout)
                raise BaseFrameworkException(msg % args)

        # metric increase
        self.inc_query_count()

        parser = self._cache.get(hash_string, None)
        if parser is not None:
            self._handle_cache_hit(hash_string)
            return parser
        else:
            # Not in cache, have to work.
            self._handle_cache_miss(hash_string)

            # Create a new instance of DocumentParser, add it to the cache
            event = threading.Event()
            self._parser_finished_events[hash_string] = event
            get_parser = self._mp_doc_parser.get_document_parser_for

            try:
                parser = get_parser(http_response)
            except:
                # Act just like when there is no parser
                msg = 'There is no parser for "%s".' % http_response.get_url()
                raise BaseFrameworkException(msg)
            else:
                save_to_cache = self.should_cache(http_response) and cache
                if save_to_cache:
                    self._cache[hash_string] = parser
                else:
                    self._handle_no_cache(hash_string)
            finally:
                event.set()
                self._parser_finished_events.pop(hash_string, None)

            return parser


@atexit.register
def cleanup_pool():
    if 'dpc' in globals():
        dpc.clear()
    

if is_main_process():
    dpc = ParserCache()
