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

from concurrent.futures import TimeoutError

# pylint: disable=E0401
from darts.lib.utils.lru import SynchronizedLRUDict
# pylint: enable=E0401

from w3af.core.controllers.threads.is_main_process import is_main_process
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.profiling.core_stats import core_profiling_is_enabled
from w3af.core.data.parsers.utils.request_uniq_id import get_request_unique_id
from w3af.core.data.parsers.mp_document_parser import mp_doc_parser
from w3af.core.data.parsers.utils.cache_stats import CacheStats
from w3af.core.data.parsers.document_parser import DocumentParser
from w3af.core.data.db.disk_set import DiskSet


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
        self._can_parse_cache = SynchronizedLRUDict(self.CACHE_SIZE * 10)
        self._parser_finished_events = {}
        self._parser_blacklist = DiskSet()

    def clear(self):
        """
        Clear all the internal variables
        :return: None
        """
        # Stop any workers
        mp_doc_parser.stop_workers()

        # Make sure the parsers clear all resources
        for parser in self._cache.itervalues():
            parser.clear()

        # We don't need the parsers anymore
        self._cache.clear()
        self._can_parse_cache.clear()

    def should_cache(self, http_response):
        """
        Defines if this http_response parser should be cached or not

        :param http_response: The http response instance
        :return: True if we should cache the parser for this response
        """
        return len(http_response.get_body()) < self.MAX_CACHEABLE_BODY_LEN

    def can_parse(self, http_response):
        """
        Check if we can parse an HTTP response

        :param http_response: The HTTP response to verify
        :return: True if we can parse this HTTP response
        """
        cached_can_parse = self._can_parse_cache.get(http_response.get_id(), default=None)

        if cached_can_parse is not None:
            return cached_can_parse

        #
        # We need to verify if we can parse this HTTP response
        #
        try:
            can_parse = DocumentParser.can_parse(http_response)
        except:
            # We catch all the exceptions here and just return False because
            # the real parsing procedure will (most likely) fail to parse
            # this response too.
            can_parse = False

        self._can_parse_cache[can_parse] = can_parse
        return can_parse

    def add_to_blacklist(self, hash_string):
        """
        Add a hash_string representing an HTTP response to the blacklist,
        indicating that we won't try to parse this response never again.

        :return: None
        """
        self._parser_blacklist.add(hash_string)

    def get_document_parser_for(self, http_response, cache=True):
        """
        Get a document parser for http_response using the cache if required

        :param http_response: The http response instance
        :param cache: If the DocumentParser is in the cache, return that one.
        :return: An instance of DocumentParser
        """
        #
        # Before doing anything too complex like caching, sending the HTTP
        # response to a different process for parsing, checking events, etc.
        # check if we can parse this HTTP response.
        #
        # This is a performance improvement that works *only if* the
        # DocumentParser.can_parse call is *fast*, which means that the
        # `can_parse` implementations of each parser needs to be fast
        #
        # It doesn't matter if we say "yes" here and then parsing exceptions
        # appear later, that should be a 1 / 10000 calls and we would still
        # be gaining a lot of performance
        #
        if not self.can_parse(http_response):
            msg = 'There is no parser for "%s".'
            raise BaseFrameworkException(msg % http_response.get_url())

        hash_string = get_request_unique_id(http_response)

        if hash_string in self._parser_blacklist:
            msg = 'Exceeded timeout while parsing "%s" in the past. Not trying again.'
            raise BaseFrameworkException(msg % http_response.get_url())

        #
        # We know that we can parse this document, lets work!
        #
        parser_finished = self._parser_finished_events.get(hash_string, None)
        if parser_finished is not None:
            # There is one subprocess already processing this http response
            # body, the best thing to do here is to make this thread wait
            # until that process has finished
            try:
                parser_finished.wait(timeout=mp_doc_parser.PARSER_TIMEOUT)
            except:
                # Act just like when there is no parser
                msg = 'There is no parser for "%s". Waited more than %s sec.'
                args = (http_response.get_url(), mp_doc_parser.PARSER_TIMEOUT)
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

            try:
                parser = mp_doc_parser.get_document_parser_for(http_response)
            except TimeoutError:
                # We failed to get a parser for this HTTP response, we better
                # ban this HTTP response so we don't waste more CPU cycles trying
                # to parse it over and over.
                self.add_to_blacklist(hash_string)

                # Act just like when there is no parser
                msg = 'Reached timeout parsing "%s".' % http_response.get_url()
                raise BaseFrameworkException(msg)
            except MemoryError:
                # We failed to get a parser for this HTTP response, we better
                # ban this HTTP response so we don't waste more CPU cycles or
                # memory trying to parse it over and over.
                self.add_to_blacklist(hash_string)

                # Act just like when there is no parser
                msg = 'Reached memory usage limit parsing "%s".' % http_response.get_url()
                raise BaseFrameworkException(msg)
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
