"""
response_cache_key.py

Copyright 2019 Andres Riancho

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
import zlib

# pylint: disable=E0401
from darts.lib.utils.lru import SynchronizedLRUDict
# pylint: enable=E0401

from w3af.core.controllers.core_helpers.not_found.response import FourOhFourResponse
from w3af.core.data.misc.xml_bones import get_xml_bones
from w3af.core.data.misc.encoding import smart_str_ignore


def get_response_cache_key(http_response,
                           clean_response=None,
                           headers=None):
    """
    Note: query.body has been cleaned by get_clean_body()

    :param http_response: The HTTP response we want to get a cache key for

    :param clean_response: The FourOhFourResponse associated with the HTTPResponse
                           passed as parameter (optional, will be calculated if not
                           provided)

    :param headers: A string containing the HTTP response headers that have to be
                    used to calculate the hash

    :return: Hash of the HTTP response body
    """
    headers = '' or headers

    #
    # Only some HTTP responses benefit from the XML-bones signature
    #
    if _should_use_xml_bones(http_response):
        body = get_xml_bones(http_response.get_body())
        normalized_path = FourOhFourResponse.normalize_path(http_response.get_uri())
    else:
        #
        # Get a clean_response if it was not provided
        #
        if clean_response is None:
            clean_response = FourOhFourResponse.from_http_response(http_response)

        body = clean_response.body
        normalized_path = clean_response.normalized_path

    #
    # Calculate the hash using all the captured information
    #
    key = ''.join([str(http_response.get_code()),
                   smart_str_ignore(normalized_path),
                   str(headers),
                   smart_str_ignore(body)])

    return quick_hash(key)


def _should_use_xml_bones(http_response):
    # Ignore small responses (the bones for this document is not so
    # representative)
    if len(http_response.get_body()) < 256:
        return False

    # Ignore large responses (might break lxml parser)
    if len(http_response.get_body()) > 1024 * 1024:
        return False

    # Check that this document is xml / html
    has_expected_content_type = False

    for content_type in ('xml', 'html'):
        if content_type in http_response.content_type:
            has_expected_content_type = True

    if not has_expected_content_type:
        return False

    # Check that it actually has tags
    if http_response.get_body().count('<') < 20:
        return False

    return True


def quick_hash(text):
    text = smart_str_ignore(text)
    return '%s%s' % (hash(text), zlib.adler32(text))


class ResponseCacheKeyCache(object):
    #
    # The memory impact of having a large number of items in this cache is
    # really low, both the keys and the values are short strings (the result of
    # quick_hash)
    #
    MAX_SIZE = 2000

    def __init__(self):
        self._cache = SynchronizedLRUDict(self.MAX_SIZE)

    def get_response_cache_key(self,
                               http_response,
                               clean_response=None,
                               headers=None):

        # When the clean response is available, use that body to calculate the
        # cache key. It has been cleaned (removed request paths and QS parameters)
        # so it has a higher chance of being equal to other responses / being
        # already in the cache
        if clean_response is not None:
            body = clean_response.body
        else:
            body = http_response.body

        cache_key = '%s%s' % (smart_str_ignore(body), headers)
        cache_key = quick_hash(cache_key)

        result = self._cache.get(cache_key, None)

        if result is not None:
            return result

        result = get_response_cache_key(http_response,
                                        clean_response=clean_response,
                                        headers=headers)

        self._cache[cache_key] = result
        return result

    def clear_cache(self):
        self._cache.clear()
