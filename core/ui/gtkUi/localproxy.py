'''
localproxy.py

Copyright 2008 Andres Riancho

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

if __name__ == '__main__':
    import sys
    sys.path.insert(0, '/home/dz0/w3af/w3af/trunk')
    
from core.controllers.daemons.proxy import proxy
from core.controllers.daemons.proxy import w3afProxyHandler
from core.data.request.fuzzableRequest import fuzzableRequest
from core.data.parsers.urlParser import getExtension
from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om

import time
import re
import Queue

IMAGE_EXTENSIONS = ['gif', 'jpg', 'jpeg', 'swf', 'png', 'bmp',  'jpe',  'ico',  'ps',  'ppm',  'tif',  'tiff']
        
class w3afLocalProxyHandler(w3afProxyHandler):
    '''
    The handler that traps requests and adds them to the queue.
    '''
    
    def doAll( self ):
        '''
        This method handles EVERY request that were send by the browser.
        '''
        # first of all, we create a fuzzable request based on the attributes that are set to this object
        fuzzReq = self._createFuzzableRequest()
        
        # Now we check if we need to add this to the queue, or just let it go through.
        if self._shouldBeTrapped(fuzzReq):
            # Add it to the request queue, and wait for the user to edit the request...
            self.server.w3afLayer._requestQueue.put(fuzzReq)
            # waiting...
            while 1:
                if id(fuzzReq) in self.server.w3afLayer._editedRequests:
                    head,  body = self.server.w3afLayer._editedRequests[ id(fuzzReq) ]
                    del self.server.w3afLayer._editedRequests[ id(fuzzReq) ]
                    self._urlOpener.sendRawRequest( head,  body )
                else:
                    time.sleep(0.3)
        else:
            # Not to be trapped, send unchanged.
            try:
                # Send the request to the remote webserver
                res = self._sendFuzzableRequest(fuzzReq)
            except Exception, e:
                self._sendError( e )
            else:
                try:
                    self._sendToBrowser( res )
                except Exception, e:
                    om.out.debug('Exception found while sending response to the browser. Exception description: ' + str(e) )        
    
    def _sendFuzzableRequest(self, fuzzReq):
        '''
        Sends a fuzzable request to the remote web server.
        '''
        url = fuzzReq.getURI()
        data = fuzzReq.getData()
        headers = fuzzReq.getHeaders()
        # Also add the cookie header.
        cookie = fuzzReq.getCookie()
        if cookie:
            headers['Cookie'] = str(cookie)

        args = ( url, )
        method = fuzzReq.getMethod()
        
        functor = getattr( self._urlOpener , method )
        # run functor , run !   ( forest gump flash )
        res = apply( functor, args, {'data': data, 'headers': headers, 'grepResult': True } ) 
        return res
    
    def _shouldBeTrapped(self, fuzzReq):
        '''
        Determine, based on the user configured parameters:
            - self._whatToTrap
            - self._trap
            - self._ignoreImages
        
        If the request needs to be trapped or not.
        @parameter fuzzReq: The request to analyze.
        '''
        if not self.server.w3afLayer._trap:
            return False
            
        if self.server.w3afLayer._ignoreImages and getExtension( fuzzReq.getURL() ).lower() in IMAGE_EXTENSIONS:
            return False
            
        if not self.server.w3afLayer._whatToTrap.search( fuzzReq.getURL() ):
            return False
        
        return True
        
    def _createFuzzableRequest(self):
        '''
        Based on the attributes, return a fuzzable request object.
        
        Important variables used here:
            - self.headers : Stores the headers for the request
            - self.rfile : A file like object that stores the postdata
            - self.path : Stores the URL that was requested by the browser
        '''
        fuzzReq = fuzzableRequest()
        fuzzReq.setURI(self.path)
        fuzzReq.setHeaders(self.headers.dict)
        fuzzReq.setMethod(self.command)
        
        # get the postdata (if any)
        if self.headers.dict.has_key('content-length'):
            # most likely a POST request
            cl = int( self.headers['content-length'] )
            postData = self.rfile.read( cl )
            fuzzReq.setData(postData)
        
        return fuzzReq


class localproxy(proxy):
    '''
    This is the local proxy server that is used by the local proxy GTK user interface to perform all its magic ;)
    '''
    
    def __init__( self, ip, port, urlOpener, proxyCert = 'core/controllers/daemons/mitm.crt' ):
        '''
        @parameter ip: IP address to bind
        @parameter port: Port to bind
        @parameter urlOpener: The urlOpener that will be used to open the requests that arrive from the browser
        @parameter proxyHandler: A class that will know how to handle requests from the browser
        @parameter proxyCert: Proxy certificate to use, this is needed for proxying SSL connections.
        '''
        proxy.__init__(self,  ip, port, urlOpener, w3afLocalProxyHandler, proxyCert)

        # Internal vars
        self._requestQueue = Queue.Queue()
        self._editedRequests = {}
        
        # User configured parameters
        self._whatToTrap= re.compile('.*')
        self._trap = True
        self._ignoreImages = True

    def getTrappedRequest(self):
        '''
        To be called by the gtk user interface every 400ms.
        @return: A fuzzable request object, or None if the queue is empty.
        '''
        return self._requestQueue.get()
        
    def getIgnoreImages(self):
        return self._ignoreImages
    
    def setIgnoreImages(self,  ignore):
        '''
        @parameter ignore: True if we want to let requests for images go through.
        '''
        self._ignoreImages = ignore
        
    def setWhatToTrap(self,  regex ):
        try:
            self._whatToTrap= re.compile(regex)
        except:
            raise w3afException('The regular expression you configured is invalid.')
        
    def setTrap(self,  trap):
        '''
        @parameter trap: True if we want to trap requests.
        '''
        self._trap = trap
        
    def getTrap(self):
        return self._trap
        
    def sendRawRequest( self, originalFuzzableRequest, head, postdata):
        self._editedRequests[ id(originalFuzzableRequest) ] = (head,  postdata)

if __name__ == '__main__':
    from core.data.url.xUrllib import xUrllib
    
    lp = localproxy('127.0.0.1', 8080, xUrllib() )
    lp.start2()
    
    for i in xrange(100):
        time.sleep(1)
        tr = lp.getTrappedRequest()
        if tr:
            print tr
            lp.sendRawRequest( tr,  tr.dumpRequestHead(), tr.getData() )
        else:
            print 'Waiting...'
        
