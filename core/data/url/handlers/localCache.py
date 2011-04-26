'''
localCache.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

from core.controllers.misc.homeDir import get_home_dir
from core.controllers.misc.number_generator import (consecutive_number_generator
                                            as core_num_gen)
from core.controllers.w3afException import w3afException
from core.data.db.history import HistoryItem
from core.data.request.frFactory import createFuzzableRequestRaw

import core.controllers.outputManager as om
import core.data.url.httpResponse as httpResponse
from core.data.parsers.urlParser import url_object


# TODO: Rethink this: why not POST?
CACHE_METHODS = ('GET', 'HEAD')

# Global cache location
CACHE_LOCATION = os.path.join(get_home_dir(), 'urllib2cache')


def gen_hash(request):
    '''
    Generate an unique ID for a request
    '''
    req = request        
    thestr = '%s%s%s%s' % (
                req.get_method(),
                req.get_full_url(),
                ''.join('%s%s' % (h, v) for h, v in req.headers.iteritems()),
                req.get_data() or '')
    return hashlib.md5(thestr).hexdigest()


class CacheHandler(urllib2.BaseHandler):
    '''
    Stores responses in a persistent on-disk cache.

    If a subsequent GET request is made for the same URL, the stored
    response is returned, saving time, resources and bandwidth

    @author: Version 0.1 by Staffan Malmgren <staffan@tomtebo.org>
    @author: Version 0.2 by Andres Riancho
    @author: Version 0.3 by Javier Andalia <jandalia =at= gmail.com>
    '''
        
    def default_open(self, request):
        
        method = request.get_method().upper()
        
        if method in CACHE_METHODS and \
        	getattr(request, 'get_from_cache', False) and \
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
        except w3afException,  w3:
            om.out.debug(str(w3))
        
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
    
    def __init__(self, request):
        self._hash_id = gen_hash(request)
        self.from_cache = True
        self.url = request.get_full_url()
        self._code = None
        self._msg = None
        self._headers = None
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
        
        @param part: Possible values: PART_HEADER, PART_BODY, PART_CODE and
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
        
        @param reqid: Request object
        @return: Boolean value
        @raises NotImplementedError: if the method is not redefined
        '''
        raise NotImplementedError

    @staticmethod
    def store_in_cache(request, response):
        '''
        Saves data in request and response objects to the cache container
        
        @param request:
        @param response:  
        @raises NotImplementedError: if the method is not redefined
        '''
        raise NotImplementedError


class DiskCachedResponse(CachedResponse):
    
    PARTS_MAPPING = {
        CachedResponse.PART_HEADER: 'headers',
        CachedResponse.PART_BODY: 'body',
        CachedResponse.PART_CODE: 'code',
        CachedResponse.PART_MSG: 'msg'
    }
    
    def _get_from_response(self, part):
        if part not in self.PARTS_MAPPING.keys():
            raise ValueError, "Unexpected value for param 'part': %s" % part
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
        except KeyboardInterrupt, e:
            raise e
        except Exception, e:
            raise w3afException(
                'localCache.py: Could not save headers file. Error: '+ str(e))
        
        try:
            body = response.read()
        except KeyboardInterrupt, e:
            raise e
        except:
            om.out.error('localCache.py: Timeout while fetching page body.')
        else:
            try:
                f = open(fname + ".body", "w")
                f.write(body)
                f.close()
            except KeyboardInterrupt, e:
                raise e
            except Exception, e:
                raise w3afException(
                    'localCache.py: Could not save body file. Error: ' + str(e))
            
        try:
            f = open(fname + ".code", "w")

            # minimal validation before storing the data to disk
            int(response.code)

            # store data to disk
            f.write(str(response.code))
            f.close()
        except KeyboardInterrupt, e:
            raise e
        except Exception, e:
            raise w3afException(
                    'localCache.py: Could not save msg file. Error: '+ str(e))
            
        try:
            f = open(fname + ".msg", "w")
            f.write(str(response.msg))
            f.close()
        except KeyboardInterrupt, e:
            raise e
        except Exception, e:
            om.out.error(
                    'localCache.py: Could not save msg file. Error: ' + str(e))
            raise e
    
    @staticmethod
    def exists_in_cache(req):
        reqid = gen_hash(req)
        exists = os.path.exists
        cache_loc = DiskCachedResponse._get_cache_location()
        reqfname = os.path.join(cache_loc, reqid)
        return exists(reqfname + ".headers") and exists(reqfname + ".body") \
                and exists(reqfname + ".code") and exists(reqfname + ".msg")


class SQLCachedResponse(CachedResponse):
    
    def __init__(self, req):
        self._hist_obj = None
        CachedResponse.__init__(self, req)
    
    def _get_from_response(self, part):
        
        hist = self._get_hist_obj()

        if part == CachedResponse.PART_HEADER:
            res = hist.info
        elif part == CachedResponse.PART_BODY:
            res = hist.response.getBody()
        elif part == CachedResponse.PART_CODE:
            res = hist.code
        elif part == CachedResponse.PART_MSG:
            res = hist.msg
        else:
            raise ValueError, "Unexpected value for param 'part': %s" % part

        return res
    
    def _get_hist_obj(self):
        hist_obj = self._hist_obj
        if hist_obj is None:
            historyobjs = HistoryItem().find([('alias', self._hash_id, "=")])
            self._hist_obj = hist_obj = historyobjs[0] if historyobjs else None
        return hist_obj
    
    @staticmethod
    def store_in_cache(request, response):
        hi = HistoryItem()
        
        # Set the request
        headers = dict(request.headers)
        headers.update(request.unredirected_hdrs)
    
        req = createFuzzableRequestRaw(method=request.get_method(),
                                      url=request.url_object,
                                      postData=request.get_data(),
                                      headers=headers)
        hi.request = req

        # Set the response
        resp = response
        code, msg, hdrs, url, body, id = (resp.code, resp.msg, resp.info(),
                                          resp.geturl(), resp.read(), resp.id)
        # BUGBUG: This is where I create/log the responses that always have
        # 0.2 as the time!
        url_instance = url_object( url )
        resp = httpResponse.httpResponse(code, body, hdrs, url_instance,
                                         request.url_object, msg=msg, id=id,
                                         alias=gen_hash(request))
        hi.response = resp

        # Now save them
        try:
            hi.save()
        except KeyboardInterrupt, k:
            raise k
        except Exception, ex:
            msg = ('Exception while inserting request/response to the '
               'database: %s\nThe request/response that generated the error is:'
               ' %s %s %s' % 
               (ex, resp.getId(), req.getURI(), resp.getCode()))
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


CacheClass = SQLCachedResponse

if not os.path.exists(CACHE_LOCATION) and CacheClass == DiskCachedResponse:
    os.makedirs(CACHE_LOCATION)

