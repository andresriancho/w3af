"""
cache_stats.py

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
import w3af.core.controllers.output_manager as om


class CacheStats(object):
    """
    Useful for sub-classing and being able to capture cache stats

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    CACHE_SIZE = 10
    DEBUG = False

    def __init__(self):
        self._from_LRU = 0.0
        self._do_not_cache = 0.0
        self._total = 0.0
        self._cache = None

    def inc_query_count(self):
        self._total += 1

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

    def _handle_cache_hit(self, hash_string):
        if self.DEBUG:
            om.out.debug('[cache] Hit for %s' % hash_string)
            self._from_LRU += 1

    def _handle_cache_miss(self, hash_string):
        if self.DEBUG:
            om.out.debug('[cache] Miss for %s' % hash_string)

    def _handle_no_cache(self, hash_string):
        if self.DEBUG:
            om.out.debug('[cache] DO NOT CACHE %s' % hash_string)
            self._do_not_cache += 1