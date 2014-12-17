"""
cached_response.py

Copyright 2013 Andres Riancho

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
import StringIO
import os
import httplib

from w3af.core.data.url.handlers.cache_backend.settings import CACHE_LOCATION
from w3af.core.data.url.handlers.cache_backend.utils import gen_hash


class CachedResponse(StringIO.StringIO):
    """
    An urllib2.response-like object for cached responses.

    To determine whether a response is cached or coming directly from
    the network, check the x-cache header rather than the object type.
    """

    PART_HEADER = 'PART_HEADER'
    PART_BODY = 'PART_BODY'
    PART_CODE = 'PART_CODE'
    PART_MSG = 'PART_MSG'
    PART_CHARSET = 'PART_CHARSET'
    PART_TIME = 'PART_TIME'

    def __init__(self, request):
        self._hash_id = gen_hash(request)
        self.from_cache = True
        self.url = request.get_full_url()
        self._code = None
        self._msg = None
        self._headers = None
        self._encoding = None
        self._time = None
        # Call parent's __init__
        self._body = self._get_from_response(CachedResponse.PART_BODY)
        StringIO.StringIO.__init__(self, self._body)

        # This kludge is necessary, do not touch!
        class PlaceHolder:
            sock = None
        self._connection = PlaceHolder()

    @property
    def code(self):
        if not self._code:
            self._code = int(self._get_from_response(CachedResponse.PART_CODE))
        return self._code

    @property
    def msg(self):
        if not self._msg:
            self._msg = self._get_from_response(CachedResponse.PART_MSG)
        return self._msg

    @property
    def encoding(self):
        if not self._encoding:
            self._encoding = self._get_from_response(CachedResponse.PART_CHARSET)
        return self._encoding

    def get_wait_time(self):
        if not self._time:
            self._time = self._get_from_response(CachedResponse.PART_TIME)
        return self._time

    def info(self):
        return self.headers()

    def headers(self):
        if not self._headers:
            headerbuf = self._get_from_response(CachedResponse.PART_HEADER)
            self._headers = httplib.HTTPMessage(StringIO.StringIO(headerbuf))
        return self._headers

    def geturl(self):
        return self.url

    def read(self):
        return self._body

    def get_full_url(self):
        return self.url

    def _get_from_response(self, part):
        """
        Return the `part` string from the saved response.

        :param part: Possible values: PART_HEADER, PART_BODY, PART_CODE and
            PART_MSG
        @raise ValueError: If `part` is not an expected value this exception
            is raised.
        """
        raise NotImplementedError

    @staticmethod
    def _get_cache_location():
        """
        Return path for cache location. Also create directory if it doesn't
        exist. For class internal use intended.
        """
        cacheloc = os.path.join(CACHE_LOCATION, str(os.getpid()))
        if not os.path.exists(cacheloc):
            os.mkdir(cacheloc)
        return cacheloc

    @staticmethod
    def exists_in_cache(request):
        """
        Verifies if a request is in the cache container

        :param reqid: Request object
        :return: Boolean value
        @raises NotImplementedError: if the method is not redefined
        """
        raise NotImplementedError

    @staticmethod
    def store_in_cache(request, response):
        """
        Saves data in request and response objects to the cache container

        :param request:
        :param response:
        @raises NotImplementedError: if the method is not redefined
        """
        raise NotImplementedError

    @staticmethod
    def init():
        """
        Takes all the actions needed for the CachedResponse class to work,
        in most cases this means creating a file, directory or database.
        """
        raise NotImplementedError

