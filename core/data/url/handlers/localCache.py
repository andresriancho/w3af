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
import urllib2
import httplib
import hashlib
from core.controllers.misc.homeDir import get_home_dir

import StringIO
import core.controllers.outputManager as om
import os.path
from core.controllers.w3afException import w3afException


CACHE_METHODS = [ 'GET' , 'HEAD' ]



def getId( request ):
    '''
    Generate an unique ID for a request
    '''
    id = ''
    id += request.get_method()
    id += request.get_full_url()
    for h in request.headers.keys():
        id += h + request.headers[h]
        
    m = hashlib.md5()
    m.update(id)
    return m.hexdigest() 

class CacheHandler(urllib2.BaseHandler):
    '''
    Stores responses in a persistant on-disk cache.

    If a subsequent GET request is made for the same URL, the stored
    response is returned, saving time, resources and bandwith

    @author: Version 0.1 by Staffan Malmgren <staffan@tomtebo.org>
    @author: Version 0.2 by Andres Riancho
    '''
    def __init__( self ):
        self.cacheLocation = get_home_dir() + os.path.sep + 'urllib2cache'
        if not os.path.exists(self.cacheLocation):
            os.makedirs(self.cacheLocation)
        
        self.cacheLocation += os.path.sep + str(os.getpid())
        if not os.path.exists(self.cacheLocation):
            os.mkdir(self.cacheLocation)
                
    def default_open(self,request):
        
        method = request.get_method().upper()
        if ( ( method in CACHE_METHODS ) and 
             ( CachedResponse.ExistsInCache(self.cacheLocation, getId( request )) )):
            try:
                cache_response_obj = CachedResponse(self.cacheLocation, request )
            except:
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
        method = request.get_method().upper()
        
        if method in CACHE_METHODS :
            id = getId( request )
            try:
                CachedResponse.StoreInCache(self.cacheLocation, id, response)
            except w3afException,  w3:
                om.out.debug( str(w3) )
        
        return response

class CachedResponse(StringIO.StringIO):
    """
    An urllib2.response-like object for cached responses.

    To determine wheter a response is cached or coming directly from
    the network, check the x-cache header rather than the object type.
    """

    def ExistsInCache(cacheLocation, id ):
        
        return (os.path.exists(cacheLocation + os.path.sep + id + ".headers") and 
                os.path.exists(cacheLocation + os.path.sep + id + ".body") and 
                os.path.exists(cacheLocation + os.path.sep + id + ".code") and 
                os.path.exists(cacheLocation + os.path.sep + id + ".msg") )
    ExistsInCache = staticmethod(ExistsInCache)

    def StoreInCache(cacheLocation, id, response):
        try:
            f = open(cacheLocation + os.path.sep + id + ".headers", "w")
            headers = str(response.info())
            f.write(headers)
            f.close()
        except KeyboardInterrupt, e:
            raise e
        except Exception, e:
            raise w3afException('localCache.py: Could not save headers file. Error: '+ str(e) )
        
        
        try:
            body = response.read()
        except KeyboardInterrupt, e:
            raise e
        except:
            om.out.error('localCache.py: Timeout while fetching page body.' )
        else:
            try:
                f = open(cacheLocation + os.path.sep + id + ".body", "w")
                f.write( body )
                f.close()
            except KeyboardInterrupt, e:
                raise e
            except Exception, e:
                raise w3afException('localCache.py: Could not save body file. Error: '+ str(e) )
            
        try:
            f = open(cacheLocation + os.path.sep + id + ".code", "w")

            # minimal validation before storing the data to disk
            int(response.code)

            # store data to disk
            f.write(str(response.code))
            f.close()
        except KeyboardInterrupt, e:
            raise e
        except:
            raise w3afException('localCache.py: Could not save msg file. Error: '+ str(e) )
            
        try:
            f = open(cacheLocation + os.path.sep + id + ".msg", "w")
            f.write(str(response.msg))
            f.close()
        except KeyboardInterrupt, e:
            raise e
        except:
            om.out.error('localCache.py: Could not save msg file. Error: '+ str(e) )
            raise e
            
    StoreInCache = staticmethod(StoreInCache)
    
    def __init__(self, cacheLocation, request ):
        self.cacheLocation = cacheLocation
        id = getId( request )
        self.id = id
        self.from_cache = True
        
        # This kludge is neccesary, do not touch!
        class placeHolder:
            sock = None
        self._connection = placeHolder()
        
        try:
            self._body = file(self.cacheLocation + os.path.sep + id+".body").read()
            StringIO.StringIO.__init__(self, self._body)

            headerbuf = file(self.cacheLocation + os.path.sep + id+".headers").read()
            self.code = int( file(self.cacheLocation + os.path.sep + id+".code").read() )
            self.msg    = file(self.cacheLocation + os.path.sep + id+".msg").read()
        except KeyboardInterrupt, e:
            raise e
        except Exception, e:
            om.out.error('localCache.py : Could not open cache for request. Error: ' + str(e) )
            raise e
        else:
            self.url = request.get_full_url()
            self.headers = httplib.HTTPMessage(StringIO.StringIO(headerbuf))

    def read(self):
        return self._body
        
    def info(self):
        return self.headers
        
    def geturl(self):
        return self.url
        
    def get_full_url(self):
        return self.url
        
