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
    
from core.controllers.daemons.proxy import proxy
from core.controllers.daemons.proxy import w3afProxyHandler

from core.data.request.fuzzableRequest import fuzzableRequest
from core.data.url.xUrllib import xUrllib

from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om

from core.data.parsers.urlParser import getExtension
from core.data.parsers.httpRequestParser import httpRequestParser

import time
import re
import Queue

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
        try:
            # Now we check if we need to add this to the queue, or just let it go through.
            if self._shouldBeTrapped(fuzzReq):
                res = self._do_trap(fuzzReq)
            else:
                # Send the request to the remote webserver
                res = self._sendFuzzableRequest(fuzzReq)
        except Exception, e:
            self._sendError( e )
        else:
            try:
                self._sendToBrowser( res )
            except Exception, e:
                om.out.debug('Exception found while sending response to the browser. Exception description: ' + str(e) )        
    
    def _do_trap(self, fuzzReq):
        # Add it to the request queue, and wait for the user to edit the request...
        self.server.w3afLayer._requestQueue.put(fuzzReq)
        # waiting...
        while 1:
            if id(fuzzReq) in self.server.w3afLayer._editedRequests:
                head,  body = self.server.w3afLayer._editedRequests[ id(fuzzReq) ]
                del self.server.w3afLayer._editedRequests[ id(fuzzReq) ]
                
                if head == body is None:
                    # The request was dropped!
                    # We close the connection to the browser and exit
                    self.rfile.close()
                    self.wfile.close()
                    break
                
                else:
                    # The request was edited by the user
                    # Send it to the remote web server and to the proxy user interface.
                    
                    if self.server.w3afLayer._fixContentLength:
                        head, body = self._fixContentLength(head, body)
                    
                    try:
                        res = self._urlOpener.sendRawRequest( head,  body )
                    except Exception,  e:
                        res = e

                    # Save it so the upper layer can read this response.
                    self.server.w3afLayer._editedResponses[ id(fuzzReq) ] = res
                    
                    # From here, we send it to the browser
                    return res
            else:
                time.sleep(0.1)
    
    def _fixContentLength(self, head, postdata):
        '''
        The user may have changed the postdata of the request, and not the content-length header;
        so we are going to fix that problem.
        '''
        fuzzReq = httpRequestParser(head, postdata)
        headers = fuzzReq.getHeaders()
        for h in headers:
            if h.lower() == 'content-length':
                length = headers[ h ]
                try:
                    length = int(length)
                except Exception,  e:
                    om.out.debug('Failed to fix the content length, the value of the header is: "'+ length +'".')
                else:
                    if length == len(fuzzReq.getData()):
                        # I don't have to fix anything
                        pass
                    else:
                        # fixing length!
                        headers[ h ] = str(len(fuzzReq.getData()))
                        fuzzReq.setHeaders(headers)
        
        head = fuzzReq.dumpRequestHead()
        return head,  postdata
    
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
            - self._methodsToTrap
            - self._whatNotToTrap
            - self._trap
        
        If the request needs to be trapped or not.
        @parameter fuzzReq: The request to analyze.
        '''

        if not self.server.w3afLayer._trap:
            return False

        if len(self.server.w3afLayer._methodsToTrap) and \
                fuzzReq.getMethod() not in self.server.w3afLayer._methodsToTrap:
            return False

        if self.server.w3afLayer._whatNotToTrap.search(fuzzReq.getURL()):
            return False

        if not self.server.w3afLayer._whatToTrap.search(fuzzReq.getURL()):
            return False

        return True


class localproxy(proxy):
    '''
    This is the local proxy server that is used by the local proxy GTK user interface to perform all its magic ;)
    '''
    
    def __init__( self, ip, port, urlOpener=xUrllib(), proxyCert='core/controllers/daemons/mitm.crt' ):
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
        self._editedResponses = {}
        
        # User configured parameters
        self._methodsToTrap = []
        self._whatToTrap = re.compile('.*')
        self._whatNotToTrap = re.compile('.*\.(gif|jpg|png|css|js|ico|swf|axd|tif)$')
        self._trap = False
        self._fixContentLength = True

    def getTrappedRequest(self):
        '''
        To be called by the gtk user interface every 400ms.
        @return: A fuzzable request object, or None if the queue is empty.
        '''
        try:
            res = self._requestQueue.get(block=False)
        except:
            return None
        else:
            return res

    def setWhatToTrap(self,  regex ):
        '''Set regular expression that indicates what URLs NOT TO trap.'''
        try:
            self._whatToTrap = re.compile(regex)
        except:
            raise w3afException('The regular expression you configured is invalid.')

    def setMethodsToTrap(self, methods):
        '''Set list that indicates what METHODS TO trap.

           If list is empty then we will trap all methods
        '''
        self._methodsToTrap = [i.upper() for i in methods]

    def setWhatNotToTrap(self, regex):
        '''Set regular expression that indicates what URLs TO trap.'''
        try:
            self._whatNotToTrap= re.compile(regex)
        except:
            raise w3afException('The regular expression you configured is invalid.')

    def setTrap(self,  trap):
        '''
        @parameter trap: True if we want to trap requests.
        '''
        self._trap = trap
        
    def getTrap(self):
        return self._trap
        
    def setFixContentLength(self,  fix):
        '''Set Fix Content Length flag.'''
        self._fixContentLength = fix
        
    def getFixContentLength(self):
        '''Get Fix Content Length flag.'''
        return self._fixContentLength
    
    def dropRequest(self,  originalFuzzableRequest):
        '''Let the handler know that the request was dropped.'''
        self._editedRequests[ id(originalFuzzableRequest) ] = (None,  None)
    
    def sendRawRequest( self, originalFuzzableRequest, head, postdata):
        # the handler is polling this dict and will extract the information from it and
        # then send it to the remote web server
        self._editedRequests[ id(originalFuzzableRequest) ] = (head,  postdata)
        
        # Loop until I get the data from the remote web server
        for i in xrange(60):
            time.sleep(0.1)
            if id(originalFuzzableRequest) in self._editedResponses:
                res = self._editedResponses[ id(originalFuzzableRequest) ]
                del self._editedResponses[ id(originalFuzzableRequest) ]
                # Now we return it...
                if isinstance(res, Exception):
                    raise res
                else:
                    return res
        
        # I looped and got nothing!
        raise w3afException('Timed out waiting for response from remote server.')

if __name__ == '__main__':
    lp = localproxy('127.0.0.1', 8080, xUrllib() )
    lp.start2()
    
    for i in xrange(10):
        time.sleep(1)
        tr = lp.getTrappedRequest()
        if tr:
            print tr
            print lp.sendRawRequest( tr,  tr.dumpRequestHead(), tr.getData() )
        else:
            print 'Waiting...'
    
    print 'Exit!'
    lp.stop()
    print 'bye bye...'
