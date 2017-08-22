"""
db.py

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
import sqlite3

import w3af.core.controllers.output_manager as om

from w3af.core.data.db.history import HistoryItem
from w3af.core.data.url.handlers.cache_backend.cached_response import CachedResponse
from w3af.core.data.url.handlers.cache_backend.utils import gen_hash
from w3af.core.data.url.HTTPResponse import HTTPResponse

from w3af.core.controllers.misc.temp_dir import create_temp_dir
from w3af.core.controllers.exceptions import ScanMustStopException


class SQLCachedResponse(CachedResponse):

    def __init__(self, req):
        self._hist_obj = None
        CachedResponse.__init__(self, req)

    def _get_from_response(self, part):

        hist = self._get_hist_obj()

        if part == CachedResponse.PART_HEADER:
            res = hist.info
        elif part == CachedResponse.PART_BODY:
            res = hist.response.body
        elif part == CachedResponse.PART_CODE:
            res = hist.code
        elif part == CachedResponse.PART_MSG:
            res = hist.msg
        elif part == CachedResponse.PART_CHARSET:
            res = hist.charset
        elif part == CachedResponse.PART_TIME:
            res = hist.time
        else:
            raise ValueError("Unexpected value for param 'part': %s" % part)

        return res

    def _get_hist_obj(self):
        hist_obj = self._hist_obj
        if hist_obj is None:
            historyobjs = HistoryItem().find([('alias', self._hash_id, "=")])
            self._hist_obj = hist_obj = historyobjs[0] if historyobjs else None
        return hist_obj

    @staticmethod
    def store_in_cache(request, response):
        # Create the http response object
        resp = HTTPResponse.from_httplib_resp(response,
                                              original_url=request.url_object)
        resp.set_id(response.id)
        resp.set_alias(gen_hash(request))

        hi = HistoryItem()
        hi.request = request
        hi.response = resp

        # Now save them
        try:
            hi.save()
        except sqlite3.Error, e:
            msg = 'A sqlite3 error was raised: "%s".' % e
            
            if 'disk' in str(e).lower():
                msg += ' Please check if your disk is full.'
                
            raise ScanMustStopException(msg)

        except Exception, ex:
            args = (ex, resp.get_id(), request.get_uri(), resp.get_code())
            msg = ('Exception while inserting request/response to the'
                   ' database: "%s". The request/response that generated'
                   ' the error is: %s %s %s')
            om.out.error(msg % args)
            raise Exception(msg % args)

    @staticmethod
    def exists_in_cache(req):
        """
        alias = gen_hash(req)
        histitem = HistoryItem()
        return bool(histitem.find([('alias', alias, "=")]))
        """
        return True

    @staticmethod
    def init():
        create_temp_dir()
        HistoryItem().init()
    
    @staticmethod
    def clear():
        """
        Clear the cache (remove all files and directories associated with it).
        """
        return HistoryItem().clear()
