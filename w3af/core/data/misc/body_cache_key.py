"""
body_cache_key.py

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

from w3af.core.controllers.misc.decorators import memoized
from w3af.core.controllers.core_helpers.not_found.response import FourOhFourResponse
from w3af.core.data.misc.xml_bones import get_xml_bones
from w3af.core.data.misc.encoding import smart_str_ignore


def get_body_cache_key(http_response,
                       clean_response=None,
                       exclude_headers=None):
    """
    Note: query.body has been cleaned by get_clean_body()

    :param http_response: The HTTP response we want to get a cache key for

    :param clean_response: The FourOhFourResponse associated with the HTTPResponse
                           passed as parameter (optional, will be calculated if not
                           provided)

    :param exclude_headers: A list of headers to exclude while creating the hash.
                            When this parameter is not None, the hash will include
                            the http response headers (keys and values) except the
                            ones in the list.

    :return: Hash of the HTTP response body
    """
    #
    # If the clean_response was not provided, we need to create one
    #
    if clean_response is None:
        clean_response = FourOhFourResponse(http_response)

    #
    # If exclude_headers is specified, use it to calculate the hash, otherwise
    # just use an empty string
    #
    exclude_headers = [] or exclude_headers
    headers = ''

    if exclude_headers:
        headers = http_response.dump_headers(exclude_headers=exclude_headers)

    #
    # Only some HTTP responses benefit from the XML-bones signature
    #
    if _should_use_xml_bones(http_response):
        body = cached_get_xml_bones(clean_response.body)
    else:
        body = clean_response.body

    #
    # Calculate the hash using all the captured information
    #
    key = '%s%s%s%s' % (http_response.get_code(),
                        smart_str_ignore(clean_response.normalized_path),
                        smart_str_ignore(headers),
                        smart_str_ignore(body))

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


@memoized
def cached_get_xml_bones(body):
    return get_xml_bones(body)
