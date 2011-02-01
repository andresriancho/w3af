'''
xUrllib.py

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

from __future__ import with_statement

import urlOpenerSettings

#
#   Misc imports
#
import core.controllers.outputManager as om
from core.controllers.misc.timeout_function import TimeLimited, TimeLimitExpired
from core.controllers.misc.lru import LRU
from core.controllers.misc.homeDir import get_home_dir
from core.controllers.misc.memoryUsage import dumpMemoryUsage
from core.controllers.misc.datastructs import deque
# This is a singleton that's used for assigning request IDs
from core.controllers.misc.number_generator import \
consecutive_number_generator as seq_gen

from core.controllers.threads.threadManager import threadManagerObj as thread_manager

from core.controllers.w3afException import w3afMustStopException, \
    w3afMustStopByUnknownReasonExc, w3afMustStopByKnownReasonExc, w3afException

#
#   Data imports
#
import core.data.parsers.urlParser as urlParser
from core.data.parsers.httpRequestParser import httpRequestParser

from core.data.request.frFactory import createFuzzableRequestRaw
from core.data.constants.httpConstants import NO_CONTENT
from core.data.url.handlers.keepalive import URLTimeoutError
from core.data.url.handlers import logHandler
from core.data.url.httpResponse import httpResponse as httpResponse
from core.data.url.HTTPRequest import HTTPRequest as HTTPRequest
from core.data.url.handlers.localCache import CachedResponse
import core.data.kb.config as cf
import core.data.kb.knowledgeBase as kb


# For subclassing requests and other things
import urllib2
import urllib

import errno
import os
import socket
import threading
import time

# for better debugging of handlers
import traceback

    
class xUrllib(object):
    '''
    This is a urllib2 wrapper.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        self.settings = urlOpenerSettings.urlOpenerSettings()
        self._opener = None
        self._cacheOpener = None
        self._memoryUsageCounter = 0
        
        # For error handling
        self._lastRequestFailed = False
        self._last_errors = deque(maxlen=10)
        self._errorCount = {}
        self._countLock = threading.RLock()
        
        self._dnsCache()
        self._tm = thread_manager
        self._sizeLRU = LRU(200)
        
        # User configured options (in an indirect way)
        self._grepPlugins = []
        self._evasionPlugins = []
        self._paused = False
        self._mustStop = False
        self._ignore_errors_conf = False
    
    def pause(self, pauseYesNo):
        '''
        When the core wants to pause a scan, it calls this method, in order to freeze all actions
        @parameter pauseYesNo: True if I want to pause the scan; False to un-pause it.
        '''
        self._paused = pauseYesNo
        
    def stop(self):
        '''
        Called when the user wants to finish a scan.
        '''
        self._mustStop = True
    
    def _callBeforeSend(self):
        '''
        This is a method that is called before every request is sent. I'm using it as
        a hook implement:
            - The pause/stop feature
            - Memory debugging features
        '''
        self._sleepIfPausedDieIfStopped()
        
        self._memoryUsageCounter += 1
        if self._memoryUsageCounter == 2000:
            dumpMemoryUsage()
            self._memoryUsageCounter = 0
    
    def _sleepIfPausedDieIfStopped(self):
        '''
        This method sleeps until self._paused is False.
        '''
        while self._paused:
            time.sleep(0.5)
            
            # The user can pause and then STOP
            if self._mustStop:
                self._mustStop = False
                self._paused = False
                # This raises a keyboard interrupt in the middle of the discovery process.
                # It has almost the same effect that a ctrl+c by the user if in consoleUi
                raise KeyboardInterrupt
        
        # The user can simply STOP the scan
        if self._mustStop:
            self._mustStop = False
            self._paused = False
            # This raises a keyboard interrupt in the middle of the discovery process.
            # It has almost the same effect that a ctrl+c by the user if in consoleUi
            # TODO: THIS SUCKS
            raise KeyboardInterrupt
    
    def end(self):
        '''
        This method is called when the xUrllib is not going to be used anymore.
        '''
        sep = os.path.sep
        try:
            cacheLocation = get_home_dir() + sep + 'urllib2cache' + sep + str(os.getpid())
            if os.path.exists(cacheLocation):
                for f in os.listdir(cacheLocation):
                    os.unlink(cacheLocation + sep + f)
                os.rmdir(cacheLocation)
        except Exception, e:
            om.out.error('Error while cleaning urllib2 cache, exception: ' + str(e))
        else:
            om.out.debug('Cleared urllib2 local cache.')
    
    def _dnsCache( self ):
        '''
        DNS cache trick
        This will speed up all the test ! Before this dns cache voodoo magic every request
        to the http server needed a dns query, this is slow on some networks so I added
        this feature.
        
        This method was taken from:
        # $Id: download.py,v 1.30 2004/05/13 09:55:30 torh Exp $
        That is part of :
        swup-0.0.20040519/
        
        Developed by:
        #  Copyright 2001 - 2003 Trustix AS - <http://www.trustix.com>
        #  Copyright 2003 - 2004 Tor Hveem - <tor@bash.no>
        #  Copyright 2004 Omar Kilani for tinysofa - <http://www.tinysofa.org>
        '''
        om.out.debug('Enabling _dnsCache()')
        
        if not hasattr( socket, 'already_configured' ):
            socket._getaddrinfo = socket.getaddrinfo
        
        _dns_cache = LRU(200)
        def _caching_getaddrinfo(*args, **kwargs):
            try:
                query = (args)
                res = _dns_cache[query]
                #This was too noisy and not so usefull
                om.out.debug('Cached DNS response for domain: ' + query[0] )
                return res
            except KeyError:
                res = socket._getaddrinfo(*args, **kwargs)
                _dns_cache[args] = res
                om.out.debug('DNS response from DNS server for domain: ' + query[0] )
                return res
        
        if not hasattr( socket, 'already_configured' ):      
            socket.getaddrinfo = _caching_getaddrinfo
            socket.already_configured = True
    
    def _init( self ):
        if self.settings.needUpdate or \
        self._opener is None or self._cacheOpener is None:
        
            self.settings.needUpdate = False
            self.settings.buildOpeners()
            self._opener = self.settings.getCustomUrlopen()
            self._cacheOpener = self.settings.getCachedUrlopen()

    def getHeaders( self, uri ):
        '''
        Returns a dict with the headers that would be used when sending a request
        to the remote server.
        '''
        req = HTTPRequest( uri )
        req = self._addHeaders( req )
        return req.headers
    
    def _isBlacklisted( self, uri ):
        '''
        If the user configured w3af to ignore a URL, we are going to be applying that configuration here.
        This is the lowest layer inside w3af.
        '''
        listOfNonTargets = cf.cf.getData('nonTargets') or []
        for u in listOfNonTargets:
            if urlParser.uri2url( uri ) == urlParser.uri2url( u ):
                msg = 'The URL you are trying to reach was configured as a non-target. ( '
                msg += uri +' ). Returning an empty response.'
                om.out.debug( msg )
                return True
        
        return False
    
    def sendRawRequest( self, head, postdata, fixContentLength=True):
        '''
        In some cases the xUrllib user wants to send a request that was typed in a textbox or is stored in a file.
        When something like that happens, this library allows the user to send the request by specifying two parameters
        for the sendRawRequest method:
        
        @parameter head: "<method> <URI> <HTTP version>\r\nHeader: Value\r\nHeader2: Value2..."
        @parameter postdata: The postdata, if any. If set to '' or None, no postdata is sent.
        @parameter fixContentLength: Indicates if the content length has to be fixed or not.
        
        @return: An httpResponse object.
        '''
        # Parse the two strings
        fuzzReq = httpRequestParser(head, postdata)
        
        # Fix the content length
        if fixContentLength:
            headers = fuzzReq.getHeaders()
            fixed = False
            for h in headers:
                if h.lower() == 'content-length':
                    headers[ h ] = str(len(postdata))
                    fixed = True
            if not fixed and postdata:
                headers[ 'content-length' ] = str(len(postdata))
            fuzzReq.setHeaders(headers)
        
        # Send it
        function_reference = getattr( self , fuzzReq.getMethod() )
        return function_reference( fuzzReq.getURI(), data=fuzzReq.getData(), headers=fuzzReq.getHeaders(),
                                                useCache=False, grepResult=False)
        
    def GET(self, uri, data='', headers={}, useCache=False, grepResult=True):
        '''
        Gets a uri using a proxy, user agents, and other settings that where
        set previously.
        
        @param uri: This is the url to GET
        @param data: Only used if the uri parameter is really a URL.
        @return: An httpResponse object.
        '''
        self._init()

        if self._isBlacklisted(uri):
            return self._new_no_content_resp(uri, log_it=True)
        
        qs = urlParser.getQueryString(uri)
        if qs:
            req = HTTPRequest(uri)
        else:
            if data:
                req = HTTPRequest(uri + '?' + data)
            else:
                # It's really an url...
                req = HTTPRequest(uri)
        req = self._addHeaders(req, headers)
        return self._send(req, useCache=useCache, grepResult=grepResult)
    
    def _new_no_content_resp(self, uri, log_it=False):
        '''
        Return a new NO_CONTENT httpResponse object. Optionally call the
        subscribed log handlers
        
        @param uri: URI string or request object
        @param log_it: Boolean that indicated whether to log request
            and response.        
        '''
        nc_resp = httpResponse(NO_CONTENT, '', {}, uri, uri, msg='No Content')
        if log_it:
            # accept a URI or a Request object
            if isinstance(uri, basestring):
                req = HTTPRequest(uri)
            else:
                req = uri
            # This also assign a the id to both objects.
            logHandler.logHandler().http_response(req, nc_resp)
        else:
            nc_resp.id = seq_gen.inc()
        return nc_resp
            
    def POST(self, uri, data='', headers={}, grepResult=True, useCache=False):
        '''
        POST's data to a uri using a proxy, user agents, and other settings
        that where set previously.
        
        @param uri: This is the url where to post.
        @param data: A string with the data for the POST.
        @return: An httpResponse object.
        '''
        self._init()
        if self._isBlacklisted(uri):
            return self._new_no_content_resp(uri, log_it=True)

        req = HTTPRequest(uri, data)
        req = self._addHeaders(req, headers)
        return self._send(req , grepResult=grepResult, useCache=useCache)

    def getRemoteFileSize( self, req, useCache=True ):
        '''
        This method was previously used in the framework to perform a HEAD request before each GET/POST (ouch!)
        and get the size of the response. The bad thing was that I was performing two requests for each resource...
        I moved the "protection against big files" to the keepalive.py module.
        
        I left it here because maybe I want to use it at some point... Mainly to call it directly or something.
        
        @return: The file size of the remote file.
        '''
        res = self.HEAD( req.get_full_url(), headers=req.headers, data=req.get_data(), useCache=useCache )  
        
        resource_length = None
        for i in res.getHeaders():
            if i.lower() == 'content-length':
                resource_length = res.getHeaders()[ i ]
                if resource_length.isdigit():
                    resource_length = int( resource_length )
                else:
                    msg = 'The content length header value of the response wasn\'t an integer...'
                    msg += ' this is strange... The value is: "' + res.getHeaders()[ i ] + '"'
                    om.out.error( msg )
                    raise w3afException( msg )
        
        if resource_length is not None:
            return resource_length
        else:
            msg = 'The response didn\'t contain a content-length header. Unable to return the'
            msg += ' remote file size of request with id: ' + str(res.id)
            om.out.debug( msg )
            # I prefer to fetch the file, before this om.out.debug was a "raise w3afException", but this didnt make much sense
            return 0
        
    def __getattr__( self, method_name ):
        '''
        This is a "catch-all" way to be able to handle every HTTP method.
        
        @parameter method_name: The name of the method being called:
        xurllib_instance.OPTIONS will make method_name == 'OPTIONS'.
        '''
        class anyMethod:
            
            class methodRequest(HTTPRequest):
                def get_method(self):
                    return self._method
                def set_method( self, method ):
                    self._method = method
            
            def __init__( self, xu, method ):
                self._xurllib = xu
                self._method = method
            
            def __call__( self, uri, data='', headers={}, useCache=False, grepResult=True ):
                
                self._xurllib._init()
                
                if self._xurllib._isBlacklisted(uri):
                    return self._xurllib._new_no_content_resp(uri, log_it=True)
            
                if data:
                    req = self.methodRequest( uri, data )
                else:
                    req = self.methodRequest( uri )
                
                req.set_method( self._method )

                if headers:
                    req = self._xurllib._addHeaders( req, headers )
                else:
                    # This adds the default headers like the user-agent,
                    # and any headers configured by the user
                    # https://sourceforge.net/tracker/?func=detail&aid=2788341&group_id=170274&atid=853652
                    req = self._xurllib._addHeaders( req, {} )
                
                return self._xurllib._send( req, useCache=useCache, grepResult=grepResult )
        
        am = anyMethod( self, method_name )
        return am

    def _addHeaders( self , req, headers={} ):
        # Add all custom Headers if they exist
        for i in self.settings.HeaderList:
            req.add_header( i[0], i[1] )
        
        for h in headers.keys():
            req.add_header( h, headers[h] )

        return req
    
    def _checkURI( self, req ):
        #bug bug !
        #
        # Reason: "unknown url type: javascript" , Exception: "<urlopen error unknown url type: javascript>"; going to retry.
        # Too many retries when trying to get: http://localhost/w3af/globalRedirect/2.php?url=javascript%3Aalert
        #
        ###TODO: The problem is that the urllib2 library fails even if i do this tests, it fails if it finds javascript: in some part of the URL    
        if req.get_full_url().startswith( 'http' ):
            return True
        elif req.get_full_url().startswith( 'javascript:' ) or req.get_full_url().startswith( 'mailto:' ):
            raise w3afException('Unsupported URL: ' +  req.get_full_url() )
        else:
            return False
            
    def _send(self, req, useCache=False, useMultipart=False, grepResult=True):
        '''
        Actually send the request object.
        
        @return: An httpResponse object.
        '''
        # This is the place where I hook the pause and stop feature
        # And some other things like memory usage debugging.
        self._callBeforeSend()

        # Sanitize the URL
        self._checkURI(req)
        
        # Evasion
        original_url = req._Request__original
        req = self._evasion(req)
        
        start_time = time.time()
        res = None
        the_opener = self._cacheOpener if useCache else self._opener
        
        try:
            res = the_opener.open(req)
        except urllib2.HTTPError, e:
            # We usually get here when response codes in [404, 403, 401,...]
            msg = '%s %s returned HTTP code "%s" - id: %s' % \
                            (req.get_method(), original_url, e.code, e.id)
            if hasattr(e, 'from_cache'):
                msg += ' - from cache.'
            om.out.debug(msg)
            
            # Return this info to the caller
            code = int(e.code)
            info = e.info()
            geturl = e.geturl()
            read = self._readRespose(e)
            httpResObj = httpResponse(code, read, info, geturl, original_url,
                                      id=e.id, time=time.time()-start_time,
                                      msg=e.msg)
            
            # Clear the log of failed requests; this request is done!
            req_id = id(req)
            if req_id in self._errorCount:
                del self._errorCount[req_id]

            # Reset errors counter
            self._zeroGlobalErrorCount()
        
            if grepResult:
                self._grepResult(req, httpResObj)
            else:
                om.out.debug(
                ('No grep for: "%s", the plugin sent grepResult=False.'
                  % geturl))
            return httpResObj
        except urllib2.URLError, e:
            # I get to this section of the code if a 400 error is returned
            # also possible when a proxy is configured and not available
            # also possible when auth credentials are wrong for the URI
            
            # Timeouts are not intended to increment the global error counter.
            # They are part of the expected behaviour.
            if not isinstance(e, URLTimeoutError):
                self._incrementGlobalErrorCount(e)
            try:
                e.reason[0]
            except:
                raise w3afException('Unexpected error in urllib2 : %s'
                                     % repr(e.reason))

            msg = ('w3af failed to reach the server while requesting:'
                  ' "%s".\nReason: "%s"; going to retry.' % 
                  (original_url, e.reason))

            # Log the errors
            om.out.debug(msg)
            om.out.debug('Traceback for this error: %s' %
                         traceback.format_exc())
            req._Request__original = original_url
            # Then retry!
            return self._retry(req, useCache)
        except KeyboardInterrupt:
            # Correct control+c handling...
            raise
        except w3afMustStopException:
            raise
        except Exception, e:
            # This except clause will catch unexpected errors
            # For the first N errors, return an empty response...
            # Then a w3afMustStopException will be raised

            msg = '%s %s returned HTTP code "%s"' % \
            (req.get_method(), original_url, NO_CONTENT)
            om.out.debug(msg)
            om.out.debug('Unhandled exception in xUrllib._send(): %s' % e)
            om.out.debug(traceback.format_exc())

            # Clear the log of failed requests; this request is done!
            req_id = id(req)
            if req_id in self._errorCount:
                del self._errorCount[req_id]
            self._incrementGlobalErrorCount(e)
            
            return self._new_no_content_resp(original_url, log_it=True)
        else:
            # Everything went well!
            rdata = req.get_data()
            if not rdata:
                msg = '%s %s returned HTTP code "%s" - id: %s' % \
                (req.get_method(), urllib.unquote_plus(original_url), res.code,
                 res.id)
            else:                
                msg = '%s %s with data: "%s" returned HTTP code "%s" - id: %s'\
                % (req.get_method(), original_url, urllib.unquote_plus(rdata),
                   res.code, res.id)

            if hasattr(res, 'from_cache'):
                msg += ' - from cache.'
            om.out.debug(msg)

            code = int(res.code)
            info = res.info()
            geturl = res.geturl()
            read = self._readRespose(res)
            httpResObj = httpResponse(code, read, info, geturl, original_url,
                                      id=res.id, time=time.time() - start_time,
                                      msg=res.msg)
            # Let the upper layers know that this response came from the local cache.
            if isinstance(res, CachedResponse):
                httpResObj.setFromCache(True)

            # Clear the log of failed requests; this request is done!
            req_id = id(req)
            if req_id in self._errorCount:
                del self._errorCount[req_id]
            self._zeroGlobalErrorCount()

            if grepResult:
                self._grepResult(req, httpResObj)
            else:
                om.out.debug('No grep for : ' + geturl + ' , the plugin sent grepResult=False.')
            return httpResObj

    def _readRespose( self, res ):
        read = ''
        try:
            read = res.read()
        except KeyboardInterrupt, k:
            raise k
        except Exception, e:
            om.out.error(str(e))
        return read
        
    def _retry(self, req, useCache):
        '''
        Try to send the request again while doing some error handling.
        '''
        req_id = id(req)
        if self._errorCount.setdefault(req_id, 1) < \
                self.settings.getMaxRetrys():
            # Increment the error count of this particular request.
            self._errorCount[req_id] += 1            
            om.out.debug('Re-sending request...')
            return self._send(req, useCache)
        else:
            error_amt = self._errorCount[req_id]
            # Clear the log of failed requests; this one definetly failed...
            del self._errorCount[req_id]
            msg = 'Too many retries (%s) while requesting: %s'  % \
                                            (error_amt, req.get_full_url())
            raise w3afException(msg)
    
    def _incrementGlobalErrorCount(self, error):
        '''
        Increment the error count, and if we got a lot of failures raise a
        "w3afMustStopException" subtype.
        
        @param error: Exception object.
        '''
        if self._ignore_errors_conf:
            return
        
        last_errors = self._last_errors

        if self._lastRequestFailed:
            last_errors.append(str(error))
        else:
            self._lastRequestFailed = True
        
        errtotal = len(last_errors)
        
        om.out.debug('Incrementing global error count. GEC: %s' % errtotal)
        
        with self._countLock:
            if errtotal >= 10 and not self._mustStop:
                # Stop using xUrllib instance
                self.stop()
                # Known reason errors. See errno module for more info on these
                # errors.
                from errno import ECONNREFUSED, EHOSTUNREACH, ECONNRESET, \
                    ENETDOWN
                EUNKNSERV = -2 # Name or service not known error
                known_errors = (EUNKNSERV, ECONNREFUSED, EHOSTUNREACH,
                                ECONNRESET, ENETDOWN)
                
                msg = ('xUrllib found too much consecutive errors. The '
                'remote webserver doesn\'t seem to be reachable anymore.')
                
                if isinstance(error, urllib2.URLError) and \
                    isinstance(error.reason, socket.error) and \
                    error.reason[0] in known_errors:
                    reason = error.reason
                    raise w3afMustStopByKnownReasonExc(msg, reason=reason)
                else:
                    raise w3afMustStopByUnknownReasonExc(msg, errs=last_errors)                    

    def ignore_errors(self, yes_no):
        '''
        Let the library know if errors should be ignored or not. Basically,
        ignore all calls to "_incrementGlobalErrorCount" and don't raise the
        w3afMustStopException.

        @parameter yes_no: True to ignore errors.
        '''
        self._ignore_errors_conf = yes_no
            
    def _zeroGlobalErrorCount( self ):
        if self._lastRequestFailed or self._last_errors:
            self._lastRequestFailed = False
            self._last_errors.clear()
            om.out.debug('Resetting global error count. GEC: 0')
    
    def setGrepPlugins(self, grepPlugins ):
        self._grepPlugins = grepPlugins
    
    def setEvasionPlugins( self, evasionPlugins ):
        # I'm sorting evasion plugins based on priority
        def sortFunc(x, y):
            return cmp(x.getPriority(), y.getPriority())
        evasionPlugins.sort(sortFunc)

        # Save the info
        self._evasionPlugins = evasionPlugins
        
    def _evasion( self, request ):
        '''
        @parameter request: HTTPRequest instance that is going to be modified
        by the evasion plugins
        '''
        for eplugin in self._evasionPlugins:
            try:
                request = eplugin.modifyRequest( request )
            except w3afException, e:
                om.out.error('Evasion plugin "'+eplugin.getName()+'" failed to modify the request. Exception: ' + str(e) )
            except Exception, e:
                raise e
                
        return request
        
    def _grepResult(self, request, response):
        # The grep process is all done in another thread. This improves the
        # speed of all w3af.
        if len( self._grepPlugins ) and urlParser.getDomain( request.get_full_url() ) in cf.cf.getData('targetDomains'):
            
            # I'll create a fuzzable request based on the urllib2 request object
            fuzzReq = createFuzzableRequestRaw( request.get_method(), request.get_full_url(), request.get_data(), request.headers )
            
            for grep_plugin in self._grepPlugins:
                #
                #   For debugging, do not remove, only comment out if needed.
                #
                self._grep_worker( grep_plugin, fuzzReq, response )
                
                # TODO: Analyze if creating a different threadpool for grep workers speeds up the whole process
                #targs = (grep_plugin, fuzzReq, response)
                #self._tm.startFunction( target=self._grep_worker, args=targs, ownerObj=self, restrict=False )
            
            self._tm.join( self )
    
    def _grep_worker( self , grep_plugin, request, response):
        '''
        This method applies the grep_plugin to a request / response pair.

        @parameter grep_plugin: The grep plugin to run.
        @parameter request: The request which generated the response. A request object.
        @parameter response: The response which was generated by the request (first parameter). A httpResponse object.
        '''
        msg = 'Starting "'+ grep_plugin.getName() +'" grep_worker for response: ' + repr(response)
        om.out.debug( msg )
        
        # Create a wrapper that will timeout in "timeout_seconds" seconds.
        #
        # TODO:
        # For now I leave it at 5, but I have to debug grep plugins and I will lower this eventually
        #
        timeout_seconds = 5
        timedout_grep_wrapper = TimeLimited( grep_plugin.grep_wrapper, timeout_seconds)
        try:
            timedout_grep_wrapper(request, response)
        except KeyboardInterrupt:
            # Correct control+c handling...
            raise
        except TimeLimitExpired:
            msg = 'The "%s" plugin took more than %s seconds to run. ' \
            'For a plugin that should only perform pattern matching, ' \
            'this is too much, please review its source code.' % \
            (grep_plugin.getName(), timeout_seconds)
            om.out.error(msg)
        except Exception, e:
            msg = 'Error in grep plugin, "%s" raised the exception: %s. ' \
            'Please report this bug to the w3af sourceforge project page ' \
            '[ https://sourceforge.net/apps/trac/w3af/newticket ] ' \
            '\nException: %s' % (grep_plugin.getName(), str(e), 
                                 traceback.format_exc(1))
            om.out.error(msg)
            om.out.error(getattr(e, 'orig_traceback_str', '') or \
                            traceback.format_exc())

        
        om.out.debug('Finished grep_worker for response: ' + repr(response))

_abbrevs = [
    (1<<50L, 'P'),
    (1<<40L, 'T'), 
    (1<<30L, 'G'), 
    (1<<20L, 'M'), 
    (1<<10L, 'k'),
    (1, '')
    ]

def greek(size):
    """
    Return a string representing the greek/metric suffix of a size
    """
    for factor, suffix in _abbrevs:
        if size > factor:
            break
    return str( int(size/factor) ) + suffix
    
