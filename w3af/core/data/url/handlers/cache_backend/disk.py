"""
disk.py

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
import os

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.exceptions import FileException

from w3af.core.data.url.handlers.cache_backend.settings import CACHE_LOCATION
from w3af.core.data.url.handlers.cache_backend.utils import gen_hash
from w3af.core.data.url.handlers.cache_backend.cached_response import CachedResponse


class DiskCachedResponse(CachedResponse):

    PARTS_MAPPING = {
        CachedResponse.PART_HEADER: 'headers',
        CachedResponse.PART_BODY: 'body',
        CachedResponse.PART_CODE: 'code',
        CachedResponse.PART_MSG: 'msg',
    }

    def _get_from_response(self, part):
        if part not in self.PARTS_MAPPING:
            raise ValueError("Unexpected value for param 'part': %s" % part)
        ext = self.PARTS_MAPPING[part]
        file = os.path.join(DiskCachedResponse._get_cache_location(),
                            '%s.%s' % (self._hash_id, ext))
        with open(file, 'r') as f:
            content = f.read()
        return content

    @staticmethod
    def store_in_cache(request, response):
        reqid = gen_hash(request)
        cache_loc = DiskCachedResponse._get_cache_location()
        fname = os.path.join(cache_loc, reqid)

        try:
            f = open(fname + ".headers", "w")
            headers = str(response.info())
            f.write(headers)
            f.close()
        except Exception, e:
            msg = 'cache.py: Could not save headers file. Exception: "%s".'
            raise FileException(msg % e)

        try:
            body = response.read()
        except Exception, e:
            om.out.error('cache.py: Timeout while fetching page body.')
        else:
            try:
                f = open(fname + ".body", "w")
                f.write(body)
                f.close()
            except Exception, e:
                msg = 'cache.py: Could not save body file. Exception: "%s".'
                raise FileException(msg % e)

        try:
            f = open(fname + ".code", "w")

            # minimal validation before storing the data to disk
            int(response.code)

            # store data to disk
            f.write(str(response.code))
            f.close()
        except Exception, e:
            msg = 'cache.py: Could not save code file. Exception: "%s".'
            raise FileException(msg % e)

        try:
            f = open(fname + ".msg", "w")
            f.write(str(response.msg))
            f.close()
        except Exception, e:
            msg = 'cache.py: Could not save msg file. Exception: "%s".'
            raise FileException(msg % e)

    @staticmethod
    def exists_in_cache(req):
        reqid = gen_hash(req)
        exists = os.path.exists
        cache_loc = DiskCachedResponse._get_cache_location()
        reqfname = os.path.join(cache_loc, reqid)
        return exists(reqfname + ".headers") and exists(reqfname + ".body") \
            and exists(reqfname + ".code") and exists(reqfname + ".msg")

    @staticmethod
    def init():
        if not os.path.exists(CACHE_LOCATION):
            os.makedirs(CACHE_LOCATION)
