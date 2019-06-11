"""
response_uniq_id.py

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
import zlib


def get_response_unique_id(http_response, prepend=None):
    """
    Before I used md5, but I realized that it was unnecessary. I
    experimented a little bit with python's hash functions and the builtin
    hash was the fastest.

    At first I thought that the built-in hash wasn't good enough, as it
    could create collisions... but... the real probability of a collision
    in the way I'm using this is too low.

    :return: The key to be used in the self._processes to identify the
             working parsers
    """
    # @see: test_bug_13_Dec_2012 to understand why we concat the uri to the
    #       body before hashing
    uri_str = http_response.get_uri().url_string.encode('utf-8')

    body_str = http_response.body or ''
    if isinstance(body_str, unicode):
        body_str = body_str.encode('utf-8', 'replace')

    _to_hash = body_str + uri_str

    # Added adler32 after finding some hash() collisions in builds
    hash_string = str(hash(_to_hash))
    hash_string += str(zlib.adler32(_to_hash))

    if prepend:
        hash_string = '%s-%s' % (prepend, hash_string)

    return hash_string


def get_body_unique_id(http_response, prepend=None):
    """
    Before I used md5, but I realized that it was unnecessary. I
    experimented a little bit with python's hash functions and the builtin
    hash was the fastest.

    At first I thought that the built-in hash wasn't good enough, as it
    could create collisions... but... the real probability of a collision
    in the way I'm using this is too low.

    :return: The key to be used in the self._processes to identify the
             working parsers
    """
    body_str = http_response.body
    if isinstance(body_str, unicode):
        body_str = body_str.encode('utf-8', 'replace')

    _to_hash = body_str

    # Added adler32 after finding some hash() collisions in builds
    hash_string = str(hash(_to_hash))
    hash_string += str(zlib.adler32(_to_hash))

    if prepend:
        hash_string = '%s-%s' % (prepend, hash_string)

    return hash_string
