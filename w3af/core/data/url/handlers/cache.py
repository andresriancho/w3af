"""
cache.py

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
import urllib2

from w3af.core.data.url.handlers.cache_backend.db import SQLCachedResponse
from w3af.core.controllers.misc.number_generator import (consecutive_number_generator
                                                         as core_num_gen)

# TODO: Why not POST? Why don't we perform real caching and respect
# the cache headers/meta tags?
# @see: https://bitbucket.org/jaraco/jaraco.net/src/65af6e442d21/jaraco/net/http/caching.py
CACHE_METHODS = ('GET', 'HEAD')


class CacheHandler(urllib2.BaseHandler):
    """
    Stores responses in a persistent on-disk cache.

    If a subsequent GET request is made for the same URL, the stored
    response is returned, saving time, resources and bandwidth

    :author: Version 0.1 by Staffan Malmgren <staffan@tomtebo.org>
    :author: Version 0.2 by Andres Riancho
    :author: Version 0.3 by Javier Andalia <jandalia =at= gmail.com>
    """
    def __init__(self):
        CacheClass.init()

    def clear(self):
        """
        Clear the cache (remove all files and directories associated with it).
        """
        return CacheClass.clear()

    def default_open(self, request):
        """
        :param request: HTTP request
        :return: None if another handler should attempt to answer this request
        """
        method = request.get_method().upper()

        if method not in CACHE_METHODS:
            return None

        if not request.get_from_cache:
            return None

        if not CacheClass.exists_in_cache(request):
            return None

        try:
            cache_response_obj = CacheClass(request)
        except Exception:
            # Sometimes the cache gets corrupted, or the initial HTTP
            # request that's saved to disk doesn't completely respect the
            # RFC and when we try to read it, it crashes.

            # Send None to the urllib2 framework, which means that we don't
            # know how to handle the request, and we forward it to the next
            # handler in the list.
            return None
        else:
            return cache_response_obj

    def http_response(self, request, response):
        # Set unique numeric identifier
        request.id = response.id = core_num_gen.inc()

        #
        # TODO: CacheHandler must be refactored. This class is doing two
        #       related but different tasks:
        #
        #           1- Storing HTTP requests and responses in a DB
        #
        #           2- Answering HTTP requests by querying the DB (caching)
        #
        #       The problem is that all HTTP responses need to be stored in the
        #       database, but only a few of those (the ones with the proper headers)
        #       need to be answered by default_open()
        #
        #       Maybe when storing the HTTP request and response we could inspect
        #       the HTTP response headers for cache indicators, and store the
        #       "can be returned from cache" boolean in a DB column
        #
        #       The new DB column would then be used by `exists_in_cache` (see
        #       above) to decide if the response should be returned from the
        #       cache
        #
        CacheClass.store_in_cache(request, response)
        return response

    https_response = http_response


# This is the default implementation
CacheClass = SQLCachedResponse
