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

import urlOpenerSettings
import core.controllers.outputManager as om
import core.data.url.timeAnalysis as timeAnalysis
from core.controllers.w3afException import *
from core.controllers.threads.threadManager import threadManager as tm
from core.data.parsers.urlParser import *
from core.data.constants.httpConstants import *

import core.data.parsers.urlParser as urlParser

from core.data.request.frFactory import createFuzzableRequestRaw

from core.data.url.httpResponse import httpResponse as httpResponse
from core.controllers.misc.lru import LRU

# For subclassing requests and other things
import urllib2
import urllib

import time
import os
from core.controllers.misc.homeDir import getHomeDir

# for better debugging of handlers
import traceback

import core.data.kb.config as cf

class sizeExceeded( Exception ):
    pass
    
class xUrllib:
    '''
    This is a urllib2 wrapper.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        self.settings = urlOpenerSettings.urlOpenerSettings()
        self._opener = None
        self._cacheOpener = None
        self._timeAnalysis = None
        # For error handling
        self._lastRequestFailed = False
        self._consecutiveErrorCount = 0
            
        self._errorCount = {}
        
        self._dnsCache()
        self._tm = tm()
        self._sizeLRU = LRU(200)
        
        # User configured options (in an indirect way)
        self._grepPlugins = []
        self._evasionPlugins = []
        
    def end( self ):
        '''
        This method is called when the xUrllib is not going to be used anymore.
        '''
        try:
            cacheLocation = getHomeDir() + os.path.sep + 'urllib2cache' + os.path.sep + str(os.getpid())
            if os.path.exists(cacheLocation):
                for f in os.listdir(cacheLocation):
                    os.unlink( cacheLocation + os.path.sep + f)
                os.rmdir(cacheLocation)
        except Exception, e:
            om.out.debug('Error while cleaning urllib2 cache, exception: ' + str(e) )
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
        import socket
        if not hasattr( socket, 'alreadyConfigured' ):
            socket._getaddrinfo = socket.getaddrinfo
        
        _dns_cache = LRU(200)
        def _caching_getaddrinfo(*args, **kwargs):
            try:
                query = (args)
                res = _dns_cache[query]
                #This was too noisy and not so usefull
                #om.out.debug('Cached DNS response for domain: ' + query[0] )
                return res
            except KeyError:
                res = socket._getaddrinfo(*args, **kwargs)
                _dns_cache[args] = res
                om.out.debug('DNS response from DNS server for domain: ' + query[0] )
                return res
        
        if not hasattr( socket, 'alreadyConfigured' ):      
            socket.getaddrinfo = _caching_getaddrinfo
            socket.alreadyConfigured = True
    
    def _init( self ):
        if self.settings.needUpdate or \
        self._opener == None or self._cacheOpener == None:
        
            self.settings.needUpdate = False
            self.settings.buildOpeners()
            self._opener = self.settings.getCustomUrlopen()
            self._cacheOpener = self.settings.getCachedUrlopen()
            self._timeAnalysis = timeAnalysis.timeAnalysis()

    def getHeaders( self, uri ):
        '''
        Returns a dict with the headers that would be used when sending a request
        to the remote server.
        '''
        req = urllib2.Request( uri )
        req = self._addHeaders( req )
        return req.headers
    
    def _isBlacklisted( self, uri ):
        '''
        If the user configured w3af to ignore a URL, we are going to be applying that configuration here.
        This is the lowest layer inside w3af.
        '''
        listOfNonTargets = cf.cf.getData('nonTargets')
        for u in listOfNonTargets:
            if urlParser.uri2url( uri ) == urlParser.uri2url( u ):
                om.out.debug('The URL you are trying to reach was configured as a non-target. ( '+uri+' ). Returning an empty response.')
                return True
        
        return False
    
    def sendRawRequest( self, head, postdata):
        '''
        In some cases the xUrllib user wants to send a request that was typed in a textbox or is stored in a file.
        When something like that happens, this library allows the user to send the request by specifying two parameters
        for the sendRawRequest method:
        
        @parameter head: The postdata, if any. If set to '' or None, no postdata is sent.
        @parameter postdata: "<method> <URI> <HTTP version>\r\nHeader: Value\r\nHeader2: Value2..."
        
        @return: An httpResponse object.
        '''
        def checkVersionSintax( version ):
            splittedVersion = version.split('/')
            if len(splittedVersion) != 2:
                # Invalid!
                raise w3afException('You are trying to send a HTTP request with an invalid version token: ' + version)
            elif len(splittedVersion) == 2:
                if splittedVersion[0].lower() != 'http':
                    raise w3afException('You are trying to send a HTTP request with an invalid HTTP token in the version specification: ' + version)
                if splittedVersion[1] not in ['1.0', '1.1']:
                    raise w3afException('You are trying to send a HTTP request with a version that is unsupported: ' + version)
            return True
        
        def checkURISintax( uri ):
            if uri.startswith('http://') and len(uri) != len('http://'):
                return True
            elif uri.startswith('https://') and len(uri) != len('https://'):
                return True
            else:
                raise w3afException('You have to specify the complete URI, including the protocol and the host. Invalid URI: ' + uri )
        
        # parse the request head
        splittedHead = head.split('\n')
        splittedHead = [ h.strip() for h in splittedHead ]
        
        # Get method, uri, version
        metUriVer = splittedHead[0]
        firstLine = metUriVer.split(' ')
        if len(firstLine) == 3:
            # Ok, we have something like "GET / HTTP/1.0"
            # Or something like "GET /hello+world.html HTTP/1.0"
            # This is the best case for us!
            method, uri, version = firstLine
            checkURISintax(uri)
            checkVersionSintax(version)
        elif len(firstLine) < 3:
            # Invalid!
            raise w3afException('You are trying to send a HTTP request with an invalid <method> <uri> <version> token: ' + metUriVer )
        elif len(firstLine) > 3:
            # This is mostly because the user sent something like this:
            # GET /hello world.html HTTP/1.0
            # Note that the correct sintax is:
            # GET /hello+world.html HTTP/1.0
            # or
            # GET /hello%20world.html HTTP/1.0
            # Mostly because we are permissive... we are going to try to send the request...
            method = firstLine[0]
            version = firstLine[-1]
            checkVersionSintax(version)
            
            # If we get here, it means that we may send the request after all...
            # FIXME: Should I encode here?
            # FIXME: Should the uri be http://host + uri ?
            uri = ' '.join( firstLine[1:-1] )
            checkURISintax(uri)
            
        # If we got here, we have a nice method, uri, version first line
        # Now we parse the headers (easy!) and finally we send the request
        headers = splittedHead[1:]
        headersDict = {}
        for h in headers:
            oneSplittedHeader = h.split(':')
            if len(oneSplittedHeader) == 2:
                headersDict[ oneSplittedHeader[0].strip() ] = oneSplittedHeader[1].strip()
            elif len(oneSplittedHeader) == 1:
                raise w3afException('You are trying to send a HTTP request with an invalid header: ' + h )
            elif len(oneSplittedHeader) > 2:
                headerValue = ' '.join(oneSplittedHeader[1:]).strip()
                headersDict[ oneSplittedHeader[0].strip() ] = headerValue
        
        # The request was parsed, now we send it to the wire!
        functionReference = getattr( self , method )
        return functionReference( uri, postdata, headers=headersDict, useCache=False, grepResult=False, getSize=False )        
        
    def GET(self, uri, data='', headers={}, useCache=False, grepResult=True, getSize=False ):
        '''
        Gets a uri using a proxy, user agents, and other settings that where set previously.
        
        @param uri: This is the url to GET
        @param data: Only used if the uri parameter is really a URL.
        @return: An httpResponse object.
        '''
        self._init()
        if self._isBlacklisted( uri ):
            return httpResponse( NO_CONTENT, '', {}, uri, uri )
        
        qs = urlParser.getQueryString( uri )
        if qs:
            req = urllib2.Request( uri )
        else:
            if data:
                req = urllib2.Request( uri + '?' + data )
            else:
                # It's really an url...
                req = urllib2.Request( uri )
            
        req = self._addHeaders( req, headers )
        
        if getSize:
            # Check the file size
            try:
                self._checkFileSize( req )
            except sizeExceeded, se:
                return httpResponse( NO_CONTENT, '', {}, uri, uri )
            except Exception, e:
                raise e
        
        return self._send( req , useCache=useCache, grepResult=grepResult)
    
    def POST(self, uri, data='', headers={}, grepResult=True, getSize=False ):
        '''
        POST's data to a uri using a proxy, user agents, and other settings that where set previously.
        
        @param uri: This is the url where to post.
        @param data: A string with the data for the POST.
        @return: An httpResponse object.
        '''
        self._init()
        if self._isBlacklisted( uri ):
            return httpResponse( NO_CONTENT, '', {}, uri, uri )
        
        req = urllib2.Request(uri, data )
        req = self._addHeaders( req, headers )
        
        if getSize:
            # Check the file size
            try:
                self._checkFileSize( req )
            except sizeExceeded, se:
                return httpResponse( NO_CONTENT, '', {}, uri, uri )
            except Exception, e:
                raise e
        
        return self._send( req , grepResult=grepResult)
    
    def getRemoteFileSize( self, uri, headers={}, useCache=True ):
        '''
        @return: The file size of the remote file.
        '''
        res = self.HEAD( uri, headers=headers, useCache=useCache )  
        
        fileLen = None
        for i in res.getHeaders():
            if i.lower() == 'content-length':
                fileLen = res.getHeaders()[ i ]
                if fileLen.isdigit():
                    fileLen = int( fileLen )
                else:
                    msg = 'The content length header value of the response wasn\'t an integer... this is strange... The value is: ' + res.getHeaders()[ i ]
                    om.out.error( msg )
                    raise w3afException( msg )
        
        if fileLen != None:
            return fileLen
        else:
            om.out.debug( 'The response didn\'t contain a content-length header. Unable to return the remote file size of request with id: ' + str(res.id) )
            # I prefer to fetch the file, before this om.out.debug was a "raise w3afException", but this didnt make much sense
            return 0
        
    def __getattr__( self, methodName ):
        '''
        This is a "catch-all" way to be able to handle every HTTP method.
        '''
        class anyMethod:
            
            class methodRequest(urllib2.Request):
                def get_method(self):
                    return self._method
                def set_method( self, method ):
                    self._method = method
            
            def __init__( self, xu, method ):
                self._xurllib = xu
                self._method = method
            
            #(self, uri, data='', headers={}, useCache=False, grepResult=True, getSize=False )
            def __call__( self, *args, **keywords ):
                if len( args ) != 1:
                    raise w3afException('Invalid number of arguments. This method receives one argument and N keywords.')
                    
                uri = args[0]
                
                self._xurllib._init()
                
                if self._xurllib._isBlacklisted( uri ):
                    return httpResponse( NO_CONTENT, '', {}, uri, uri )
            
                if 'data' in keywords and keywords['data'] != None:
                    req = self.methodRequest( uri, keywords['data'] )
                    keywords.pop('data')
                else:
                    req = self.methodRequest( uri )
                
                req.set_method( self._method )

                if 'headers' in keywords:
                    req = self._xurllib._addHeaders( req, keywords['headers'] )
                    keywords.pop('headers')
                
                om.out.debug( req.get_method() + ' ' + uri)
                
                # def _send( self , req , useCache=False, useMultipart=False, grepResult=True )
                return self._xurllib._send( req, keywords )
        
        am = anyMethod( self, methodName )
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
        #[ Fri Sep 21 23:05:18 2007 - debug ] Reason: "unknown url type: javascript" , Exception: "<urlopen error unknown url type: javascript>"; going to retry.
        #[ Fri Sep 21 23:05:18 2007 - error ] Too many retries when trying to get: http://localhost/w3af/globalRedirect/2.php?url=javascript%3Aalert
        #
        ###TODO: The problem is that the urllib2 library fails even if i do this tests, it fails if it finds javascript: in some part of the URL    
        if req.get_full_url().startswith( 'http' ):
            return True
        elif req.get_full_url().startswith( 'javascript:' ) or req.get_full_url().startswith( 'mailto:' ):
            raise w3afException('Unsupported URL: ' +  req.get_full_url() )
        else:
            return False
    
    def _checkFileSize( self, req ):
        # No max file size.
        if self.settings.getMaxFileSize() == 0:
            pass
        else:
            # This will speed up the most frequent request, no HEAD is done to the last recently used URL's
            if req.get_full_url() not in self._sizeLRU:
                size = self.getRemoteFileSize( req.get_full_url() )
                self._sizeLRU[ req.get_full_url() ] = size
            else:
                size = self._sizeLRU[ req.get_full_url() ]
                #om.out.debug('Size of response got from self._sizeLRU.')
            
            if self.settings.getMaxFileSize() < size :
                msg = 'File size of URL: ' +  req.get_full_url()  + ' exceeds the configured file size limit. Max size limit is: ' + str(greek(self.settings.getMaxFileSize())) + ' and file size is: ' + str(greek(size)) + ' .'
                om.out.debug( msg )
                raise sizeExceeded( msg )
            
    def _send( self , req , useCache=False, useMultipart=False, grepResult=True ):
        # Sanitize the URL
        self._checkURI( req )
        
        # Evasion
        originalUrl = req._Request__original
        req = self._evasion( req )
        
        startTime = time.time()
        res = None
        try:
            if useCache:
                res = self._cacheOpener.open( req )
            else:
                res = self._opener.open( req )
        except urllib2.URLError, e:
            # I get to this section of the code if a 400 error is returned
            # also possible when a proxy is configured and not available
            # also possible when auth credentials are wrong for the URI
            if hasattr(e, 'reason'):
                self._incrementGlobalErrorCount()
                try:
                    e.reason[0]
                except:
                    raise w3afException('Unexpected error in urllib2 / httplib: ' + repr(e.reason) )                    
                else:
                    if e.reason[0] == -2:
                        raise w3afException('Failed to resolve domain name for URL: ' + req.get_full_url() )
                    if e.reason[0] == 111:
                        raise w3afException('Connection refused while requesting: ' + req.get_full_url() )
                    else:
                        om.out.debug( 'w3af failed to reach the server while requesting: "'+originalUrl+'".\nReason: "' + str(e.reason) + '" , Exception: "'+ str(e)+'"; going to retry.')
                        om.out.debug( 'Traceback for this error: ' + str( traceback.format_exc() ) )
                        req._Request__original = originalUrl
                        return self._retry( req, useCache )
            elif hasattr(e, 'code'):
                # We usually get here when the response has codes 404, 403, 401, etc...
                om.out.debug( req.get_method() + ' ' + originalUrl +' returned HTTP code "' + str(e.code) + '"' )
                
                # Return this info to the caller
                code = int(e.code)
                info = e.info()
                geturl = e.geturl()
                read = self._readRespose( e )
                httpResObj = httpResponse(code, read, info, geturl, originalUrl, id=e.id, time=time.time() - startTime )
                
                # Clear the log of failed requests; this request is done!
                if id(req) in self._errorCount:
                    del self._errorCount[ id(req) ]
                self._decrementGlobalErrorCount()
            
                if grepResult:
                    self._grepResult( req, httpResObj )
                else:
                    om.out.debug('No grep for : ' + geturl + ' , the plugin sent grepResult=False.')
                return httpResObj
        except KeyboardInterrupt, k:
            # Correct control+c handling...
            raise k
        except Exception, e:
            # This except clause will catch errors like 
            # "(-3, 'Temporary failure in name resolution')"
            # "(-2, 'Name or service not known')"
            # The handling of this errors is complex... if I get a lot of errors in a row, I'll raise a
            # w3afMustStopException because the remote webserver might be unreachable.
            # For the first N errors, I just return an empty response...
            om.out.debug( req.get_method() + ' ' + originalUrl +' returned HTTP code "' + str(NO_CONTENT) + '"' )
            om.out.debug( 'Unhandled exception in xUrllib._send(): ' + str ( e ) )
            om.out.debug( str( traceback.format_exc() ) )
            
            # Clear the log of failed requests; this request is done!
            if id(req) in self._errorCount:
                del self._errorCount[ id(req) ]
            self._incrementGlobalErrorCount()
            
            return httpResponse( NO_CONTENT, '', {}, originalUrl, originalUrl )
        else:
            # Everything ok !
            if not req.get_data():
                om.out.debug( req.get_method() + ' ' + urllib.unquote_plus( originalUrl ) +' returned HTTP code "' + str(res.code) + '"' )
            else:
                om.out.debug( req.get_method() + ' ' + originalUrl +' with data: "'+ urllib.unquote_plus( req.get_data() ) +'" returned HTTP code "' + str(res.code) + '"' )
                
            code = int(res.code)
            info = res.info()
            geturl = res.geturl()
            read = self._readRespose( res )
            httpResObj = httpResponse(code, read, info, geturl, originalUrl, id=res.id, time=time.time() - startTime )
            
            # Clear the log of failed requests; this request is done!
            if id(req) in self._errorCount:
                del self._errorCount[ id(req) ]
            self._decrementGlobalErrorCount()
            
            if grepResult:
                self._grepResult( req, httpResObj )
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
            om.out.error( str ( e ) )
            return read
        return read
        
    def _retry( self, req , useCache ):
        '''
        Try to send the request again while doing some error handling.
        '''
        if self._errorCount.get( id(req), 0 ) < self.settings.getMaxRetrys() :
            # Increment the error count of this particular request.
            if id(req) not in self._errorCount:
                self._errorCount[ id(req) ] = 0
            self._errorCount[ id(req) ] += 1
            
            om.out.debug('Re-sending request...')
            return self._send( req, useCache )
        else:
            # Clear the log of failed requests; this one definetly failed...
            del self._errorCount[ id(req) ]
            self._incrementGlobalErrorCount()
            raise w3afException('Too many retries when trying to get: ' + req.get_full_url() )
    
    def _incrementGlobalErrorCount( self ):
        if self._lastRequestFailed:
            self._consecutiveErrorCount += 1
        else:
            self._lastRequestFailed = True
        
        om.out.debug('Incrementing global error count. GEC: ' + str(self._consecutiveErrorCount))
        
        if self._consecutiveErrorCount >= 10:
            raise w3afMustStopException('The xUrllib found too much consecutive errors. The remote webserver doesn\'t seem to be reachable anymore; please verify manually.')
            
    def _decrementGlobalErrorCount( self ):
        self._lastRequestFailed = False
        self._consecutiveErrorCount = 0
        om.out.debug('Decrementing global error count. GEC: ' + str(self._consecutiveErrorCount))
    
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
        @parameter request: urllib2.Request instance that is going to be modified by the evasion plugins
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
        # The grep process is all done in another thread. This improved the
        # speed of all w3af.
        if len( self._grepPlugins ) and urlParser.getDomain( request.get_full_url() ) in cf.cf.getData('targetDomains'):
            # I'll create a fuzzable request based on the urllib2 request object
            fuzzReq = createFuzzableRequestRaw( request.get_method(), request.get_full_url(), request.get_data(), request.headers )
            targs = (fuzzReq, response)
            self._tm.startFunction( target=self._grepWorker, args=targs, ownerObj=self )
    
    def _grepWorker( self , request, response):
        om.out.debug('Starting grepWorker for response: ' + repr(response) )
        
        for grepPlugin in self._grepPlugins:
            try:
                grepPlugin.testResponse( request, response)
            except KeyboardInterrupt:
                # Correct control+c handling...
                raise
            except Exception, e:
                om.out.error( 'Error in grep plugin, "' + grepPlugin.getName() + '" raised the exception: ' + str(e) + '. Please report this bug. Exception: ' + str(traceback.format_exc(1)) )
                om.out.debug( str(traceback.format_exc()) )
        
        om.out.debug('Finished grepWorker for response: ' + repr(response) )

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
    
