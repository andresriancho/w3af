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

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.threads.is_main_process import is_main_process
from w3af.core.controllers.profiling.core_stats import core_profiling_is_enabled
from w3af.core.controllers.exceptions import (BaseFrameworkException,
                                              ScanMustStopException)

from w3af.core.data.parsers.mp_document_parser import mp_doc_parser
from w3af.core.data.parsers.utils.cache_stats import CacheStats
from w3af.core.data.parsers.document_parser import DocumentParser
from w3af.core.data.db.disk_set import DiskSet
from w3af.core.data.parsers.utils.response_uniq_id import (get_response_unique_id,
                                                           get_body_unique_id)


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
        om.out.debug('Called clear() on ParserCache')

        # Stop any workers
        mp_doc_parser.stop_workers()

        # Make sure the parsers clear all resources
        for parser in self._cache.itervalues():
            if hasattr(parser, 'clear'):
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
        Get a document parser for http_response using the cache if possible

        :param http_response: The http response instance
        :param cache: True if the document parser should be saved to the cache
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

        hash_string = get_response_unique_id(http_response)

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
            wait_result = parser_finished.wait(timeout=mp_doc_parser.PARSER_TIMEOUT)
            if not wait_result:
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
            except ScanMustStopException, e:
                msg = 'The document parser is in an invalid state! %s'
                raise ScanMustStopException(msg % e)
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

    def _log_return_empty(self, http_response, detail):
        msg = 'Returning empty list in get_tags_by_filter("%s"). '
        msg += detail
        om.out.debug(msg % http_response.get_uri())

    def get_tags_by_filter(self, http_response, tags, yield_text=False, cache=True):
        """
        Get specific tags from http_response using the cache if possible

        :param http_response: The http response instance
        :param tags: List of tags to get, or None if all tags should be returned
        :param yield_text: Include the tag text (<a>text</a>)
        :param cache: True if the document parser should be saved to the cache
        :return: An instance of DocumentParser
        """
        #
        # This is a performance hack that should reduce the time consumed by
        # this method without impacting its results. Note that in HTML this is
        # valid:
        #
        #   <script
        #
        # And this is invalid:
        #
        #   < script
        #
        # We use that in order to speed-up this function
        #
        if tags is not None:
            body_lower = http_response.get_body().lower()

            for tag in tags:
                lt_tag = '<%s' % tag
                if lt_tag in body_lower:
                    break
            else:
                # No tag was found in the HTML
                return []

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
            self._log_return_empty(http_response, 'No parser available')
            return []

        args = '%r%r' % (tags, yield_text)
        hash_string = get_body_unique_id(http_response, prepend=args)

        if hash_string in self._parser_blacklist:
            self._log_return_empty(http_response, 'HTTP response is blacklisted')
            return []

        #
        # We know that we can parse this document, lets work!
        #
        parser_finished = self._parser_finished_events.get(hash_string, None)
        if parser_finished is not None:
            # There is one subprocess already processing this http response
            # body, the best thing to do here is to make this thread wait
            # until that process has finished
            wait_result = parser_finished.wait(timeout=mp_doc_parser.PARSER_TIMEOUT)
            if not wait_result:
                # Act just like when there is no parser
                self._log_return_empty(http_response, 'Timeout waiting for response')
                return []

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
                tags = mp_doc_parser.get_tags_by_filter(http_response,
                                                        tags,
                                                        yield_text=yield_text)
            except TimeoutError:
                # We failed to get a parser for this HTTP response, we better
                # ban this HTTP response so we don't waste more CPU cycles trying
                # to parse it over and over.
                self.add_to_blacklist(hash_string)

                # Act just like when there is no parser
                self._log_return_empty(http_response, 'Timeout waiting for get_tags_by_filter()')
                return []
            except MemoryError:
                # We failed to get a parser for this HTTP response, we better
                # ban this HTTP response so we don't waste more CPU cycles or
                # memory trying to parse it over and over.
                self.add_to_blacklist(hash_string)

                # Act just like when there is no parser
                self._log_return_empty(http_response, 'Reached memory usage limit')
                return []
            except ScanMustStopException, e:
                msg = 'The document parser is in an invalid state! %s'
                raise ScanMustStopException(msg % e)
            except Exception, e:
                # Act just like when there is no parser
                msg = 'Unhandled exception running get_tags_by_filter("%s"): %s'
                args = (http_response.get_url(), e)
                raise BaseFrameworkException(msg % args)
            else:
                if cache:
                    self._cache[hash_string] = tags
                else:
                    self._handle_no_cache(hash_string)
            finally:
                event.set()
                self._parser_finished_events.pop(hash_string, None)

            return tags


@atexit.register
def cleanup_pool():
    if 'dpc' in globals():
        dpc.clear()
    

if is_main_process():
    dpc = ParserCache()
