'''
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

'''
import httplib
import hashlib
import os.path
import StringIO
import urllib2

import core.controllers.output_manager as om

from core.controllers.misc.temp_dir import create_temp_dir
from core.controllers.misc.homeDir import get_home_dir
from core.controllers.misc.number_generator import (consecutive_number_generator
                                                    as core_num_gen)
from core.controllers.exceptions import FileException
from core.data.db.history import HistoryItem
from core.data.url.HTTPResponse import HTTPResponse

# TODO: Why not POST? Why don't we perform real caching and respect
# the cache headers/meta tags?
# @see: https://bitbucket.org/jaraco/jaraco.net/src/65af6e442d21/jaraco/net/http/caching.py
CACHE_METHODS = ('GET', 'HEAD')

# Global cache location
CACHE_LOCATION = os.path.join(get_home_dir(), 'urllib2cache')


def gen_hash(request):
    '''
    Generate an unique ID for a request
    '''
    req = request
    headers_1 = ''.join('%s%s' % (h, v) for h, v in req.headers.iteritems())
    headers_2 = ''.join('%s%s' % (h, v) for h, v in req.unredirected_hdrs.iteritems())
    
    the_str = '%s%s%s%s%s' % (
                             req.get_method(),
                             req.get_full_url(),
                             headers_1,
                             headers_2,
                             req.get_data() or ''
                             )
    
    the_str = the_str.encode('utf-8', 'ignore')
    return hashlib.md5(the_str).hexdigest()


class CacheHandler(urllib2.BaseHandler):
    '''
    Stores responses in a persistent on-disk cache.

    If a subsequent GET request is made for the same URL, the stored
    response is returned, saving time, resources and bandwidth

    :author: Version 0.1 by Staffan Malmgren <staffan@tomtebo.org>
    :author: Version 0.2 by Andres Riancho
    :author: Version 0.3 by Javier Andalia <jandalia =at= gmail.com>
    '''
    def __init__(self):
        CacheClass.init()

    def clear(self):
        '''
        Clear the cache (remove all files and directories associated with it).
        '''
        return CacheClass.clear()

    def default_open(self, request):

        method = request.get_method().upper()

        if method in CACHE_METHODS and \
        request.get_from_cache and \
        CacheClass.exists_in_cache(request):
            try:
                cache_response_obj = CacheClass(request)
            except Exception:
                # Sometimes the cache gets corrupted, or the initial HTTP request
                # that's saved to disk doesn't completely respect the RFC and
                # when we try to read it, it crashes.

                # Send None to the urllib2 framework, which means that we don't
                # know how to handle the request, and we forward it to the next
                # handler in the list.
                return None
            else:
                return cache_response_obj
        else:
            # Let the next handler try to handle the request
            return None

    def http_response(self, request, response):
        # Set unique numeric identifier
        request.id = response.id = core_num_gen.inc()
        try:
            CacheClass.store_in_cache(request, response)
        except FileException, fe:
            om.out.debug(str(fe))

        return response

    https_response = http_response


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

    def __init__(self, request):
        self._hash_id = gen_hash(request)
        self.from_cache = True
        self.url = request.get_full_url()
        self._code = None
        self._msg = None
        self._headers = None
        self._encoding = None
        # Call parent's __init__
        self._body = self._get_from_response(CachedResponse.PART_BODY)
        StringIO.StringIO.__init__(self, self._body)

        # This kludge is necessary, do not touch!
        class placeHolder:
            sock = None
        self._connection = placeHolder()

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
            self._encoding = self._get_from_response(
                CachedResponse.PART_CHARSET)
        return self._encoding

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
        '''
        Return the `part` string from the saved response.

        :param part: Possible values: PART_HEADER, PART_BODY, PART_CODE and
            PART_MSG
        @raise ValueError: If `part` is not an expected value this exception
            is raised.
        '''
        raise NotImplementedError

    @staticmethod
    def _get_cache_location():
        '''
        Return path for cache location. Also create directory if it doesn't
        exist. For class internal use intended.
        '''
        cacheloc = os.path.join(CACHE_LOCATION, str(os.getpid()))
        if not os.path.exists(cacheloc):
            os.mkdir(cacheloc)
        return cacheloc

    @staticmethod
    def exists_in_cache(request):
        '''
        Verifies if a request is in the cache container

        :param reqid: Request object
        :return: Boolean value
        @raises NotImplementedError: if the method is not redefined
        '''
        raise NotImplementedError

    @staticmethod
    def store_in_cache(request, response):
        '''
        Saves data in request and response objects to the cache container

        :param request:
        :param response:
        @raises NotImplementedError: if the method is not redefined
        '''
        raise NotImplementedError

    @staticmethod
    def init():
        '''
        Takes all the actions needed for the CachedResponse class to work,
        in most cases this means creating a file, directory or databse.
        '''
        raise NotImplementedError


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
        except Exception, ex:
            msg = ('Exception while inserting request/response to the'
                   ' database: %s\nThe request/response that generated'
                   ' the error is: %s %s %s' %
                   (ex, resp.get_id(), request.get_uri(), resp.get_code()))
            om.out.error(msg)
            raise

    @staticmethod
    def exists_in_cache(req):
        '''
        alias = gen_hash(req)
        histitem = HistoryItem()
        return bool(histitem.find([('alias', alias, "=")]))
        '''
        return True

    @staticmethod
    def init():
        create_temp_dir()
        HistoryItem().init()
    
    @staticmethod
    def clear():
        '''
        Clear the cache (remove all files and directories associated with it).
        '''
        return HistoryItem().clear()

# This is the default implementation
CacheClass = SQLCachedResponse
