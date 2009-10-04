'''
fingerprint404Page.py

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

import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb
import core.data.kb.config as cf
import core.data.parsers.urlParser as urlParser
from core.data.fuzzer.fuzzer import createRandAlpha, createRandAlNum
from core.controllers.w3afException import w3afException, w3afMustStopException
from core.controllers.misc.levenshtein import relative_distance
from core.controllers.misc.lru import LRU
import urllib
import cgi

IS_EQUAL_RATIO = 0.90


class fingerprint404Page:
    '''
    Read the 404 page returned by the server.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self, uriOpener):
        self._urlOpener =  uriOpener
        
        self._404_page_LRU = LRU(250)
        self._LRU_append_id = 0
        
        # This is gooood! It will put the function in a place that's available for all.
        kb.kb.save( 'error404page', '404', self.is404 )

        # Only report once
        self._reported = False
        self._alreadyAnalyzed = False

    def _append_to_LRU(self, obj):
        '''
        Appends obj to the self._404_page_LRU
        '''
        self._LRU_append_id += 1
        self._404_page_LRU[ self._LRU_append_id ] = obj

    def _get_clean_body(self, response):
        '''
        Definition of clean in this method:
            - input:
                - response.getURL() == http://host.tld/aaaaaaa/
                - response.getBody() == 'spam aaaaaaa eggs'
                
            - output:
                - self._clean_body( response ) == 'spam  eggs'
        
        The same works with filenames.
        All of them, are removed encoded and "as is".
        
        @parameter response: The httpResponse object to clean
        @return: A string that represents the "cleaned" response body of the response.
        '''
        original_body = response.getBody()
        url = response.getURL()
        to_replace = url.split('/')
        to_replace.append( url )
        
        for i in to_replace:
            if len(i) > 6:
                original_body = original_body.replace(i, '')
                original_body = original_body.replace(urllib.unquote_plus(i), '')
                original_body = original_body.replace(cgi.escape(i), '')
                original_body = original_body.replace(cgi.escape(urllib.unquote_plus(i)), '')

        return original_body
        
    def _add404Knowledge( self, httpResponse ):
        '''
        Creates a (response, extension) tuple and saves it in the self._404_page_LRU.
        '''
        try:
            response, extension = self._generate404( httpResponse.getURL() )
        except w3afException, w3:
            om.out.debug('w3afException in _generate404:' + str(w3) )
            raise w3
        except KeyboardInterrupt, k:
            raise k
        except w3afMustStopException:
            # Someone else will raise this exception and handle it as expected
            # whenever the next call to GET is done
            raise w3afException('w3afMustStopException found by _generate404, someone else will handle it.')
        except Exception, e:
            om.out.debug('Something went wrong while getting a 404 page...')
            raise e
        else:
            if response.getCode() not in [404, 401, 403] and not self._reported:
                # Not using 404 in error pages
                om.out.information('Server uses ' + str(response.getCode()) + ' instead of HTTP 404 error code. ')
                self._reported = True
            
            # This fixes some problems with redirections and with pykto that
            # sends requests to http://host// which is != from http://host/
            # This fixes bug #2020211
            response.setURL( httpResponse.getURL() )

            self._append_to_LRU( (response, extension) )
    
    def _byDirectory( self, httpResponse ):
        '''
        @return: True if the httpResponse is a 404 based on the knowledge found by _add404Knowledge and the data
        in _404pageList regarding the directory.
        '''
        tmp = [ response.getBody() for (response, extension) in self._404_page_LRU.values() if \
        urlParser.getDomainPath(httpResponse.getURL()) == urlParser.getDomainPath(response.getURL())]
        
        if len( tmp ):
            # All items in this directory should be the same...
            response_body = tmp[0]
            html_body = self._get_clean_body( httpResponse )
            ratio = relative_distance( response_body, html_body )
            if ratio > IS_EQUAL_RATIO:
                om.out.debug(httpResponse.getURL() + ' is a 404 (_byDirectory).' + str(ratio) + ' > ' + str(IS_EQUAL_RATIO) )
                return True
            else:
                return False
        else:
            try:
                self._add404Knowledge( httpResponse )
            except w3afException:
                # bleh! I don't like this... but I only get here if there was an error in the _add404Knowledge ;
                # which is really uncommon
                return httpResponse.getCode() == 404
            else:
                return self._byDirectory( httpResponse )
    
    def _byDirectoryAndExtension( self, httpResponse ):
        '''
        @return: True if the httpResponse is a 404 based on the knowledge found by _add404Knowledge and the data
        in _404pageList regarding the directory AND the file extension.
        '''
        tmp = [ response.getBody() for (response, extension) in self._404_page_LRU.values() if \
        urlParser.getDomainPath(httpResponse.getURL()) == urlParser.getDomainPath(response.getURL()) and \
        (urlParser.getExtension(httpResponse.getURL()) == '' or urlParser.getExtension(httpResponse.getURL()) == extension)]

        if len( tmp ):
            # All items in this directory/extension combination should be the same...
            response_body = tmp[0]
            html_body = self._get_clean_body( httpResponse )
            
            ratio = relative_distance( response_body, html_body )
            
            '''
            print '=' * 60
            print 'Comparing URL', httpResponse.getURL()
            print '=' * 60
            print repr(response_body)
            print '=' * 60
            print repr(html_body)
            print '=' * 60
            print ratio
            print '=' * 60
            '''
            
            if ratio > IS_EQUAL_RATIO:
                msg = httpResponse.getURL() + ' is a 404 (_byDirectoryAndExtension). ' + str(ratio)
                msg += ' > ' + str(IS_EQUAL_RATIO)
                om.out.debug( msg )
                return True
            else:
                return False
        else:
            try:
                self._add404Knowledge( httpResponse )
            except w3afException:
                # bleh! I don't like this... but I only get here if there was an error in the _add404Knowledge ;
                # which is really uncommon
                return httpResponse.getCode() == 404
            else:
                return self._byDirectoryAndExtension( httpResponse )
            
    def is404( self, httpResponse ):
        if not self._alreadyAnalyzed:
            try:
                self._add404Knowledge( httpResponse )
            except w3afException:
                om.out.debug('Failed to add 404 knowledge for ' + str(httpResponse) )
        
        # Set a variable that is widely used
        domainPath = urlParser.getDomainPath( httpResponse.getURL() )
        
        # Check for the fixed responses
        if domainPath in cf.cf.getData('always404'):
            return True
        elif domainPath in cf.cf.getData('404exceptions'):
            return False
          
        # Start the fun.
        if cf.cf.getData('autodetect404'):
            print 'autodetect'
            return self._autodetect( httpResponse )
        elif cf.cf.getData('byDirectory404'):
            return self._byDirectory( httpResponse )
        # worse case
        elif cf.cf.getData('byDirectoryAndExtension404'):
            return self._byDirectoryAndExtension( httpResponse )
        
    def _autodetect( self, httpResponse ):
        '''
        Try to autodetect how I'm going to handle the 404 messages
        
        @parameter httpResponse: The httpResponse, with the whole response information.
        @return: True if the response is a 404.
        '''
        if len( self._404_page_LRU ) <= 25:
            msg = 'I can\'t perform autodetection yet (404pageList has '
            msg += str(len(self._404_page_LRU))+' items). Keep on working with the worse case'
            om.out.debug( msg )
            return self._byDirectoryAndExtension( httpResponse )
        else:
            if not self._alreadyAnalyzed:
                om.out.debug('Starting analysis of responses.')
                self._analyzeData()
                self._alreadyAnalyzed = True
            
            # Now return a response
            if kb.kb.getData('error404page', 'trust404'):
                if httpResponse.getCode() == 404:
                    om.out.debug(httpResponse.getURL() + ' is a 404 (_autodetect trusting 404).')
                    return True
                else:
                    return False
            elif kb.kb.getData('error404page', 'trustBody'):
                html_body = self._get_clean_body( httpResponse )
                ratio = relative_distance( html_body, kb.kb.getData('error404page', 'trustBody') )
                if ratio > IS_EQUAL_RATIO:
                    msg = httpResponse.getURL() + ' is a 404 (_autodetect trusting body). '
                    msg += str(ratio) + ' > ' + str(IS_EQUAL_RATIO)
                    om.out.debug( msg )
                    return True
                else:
                    return False
            else:
                # worse case
                return self._byDirectoryAndExtension( httpResponse )
            
    def _analyzeData( self ):
        # Check if all 404 responses are really HTTP 404
        tmp = [ (response, extension) for (response, extension) in self._404_page_LRU.values() if response.getCode() == 404 ]
        if len(tmp) == len(self._404_page_LRU):
            om.out.debug('The remote website uses 404 HTTP response code as 404.')
            kb.kb.save('error404page', 'trust404', True)
            return
        else:
            om.out.debug('The remote website DOES NOT use 404 HTTP response code as 404.')
            
        # Check if the 404 error message body is the same for all directories
        def areEqual( tmp, exactComparison=False ):
            for a in tmp:
                for b in tmp:
                    
                    # The first method
                    if exactComparison == True:
                        if a != b:
                            return False
                    
                    # The second method
                    if exactComparison == False:
                        if relative_distance( a, b ) < IS_EQUAL_RATIO:
                            # If one is different, then we return false.
                            return False
                        
            return True
        
        # Now I check if all responses have the same extension (which is bad for the analysis)
        # If they all have the same extension, I'll create a new one with a different extension
        extensionList = [ extension for (response, extension) in self._404_page_LRU.values() ]
        if areEqual( extensionList, exactComparison=True ):
            responseCopy = response.copy()
            responseURL = response.getURL()
            extension = urlParser.getExtension( responseURL )
            fakedURL = responseURL[0:len(responseURL)-len(extension)] + createRandAlpha(3)
            responseCopy.setURL(fakedURL)
            self._add404Knowledge(responseCopy)
        
        tmp = [ response.getBody() for (response, extension) in self._404_page_LRU.values() ]
        if areEqual( tmp ):
            om.out.debug('The remote web site uses always the same body for all 404 responses.')
            kb.kb.save('error404page', 'trustBody', tmp[0] )
            return
            
        # hmmm... I have nothing else to analyze... if I get here it means that the web application is wierd and
        # nothing will help me detect 404 pages...
        
    def getName( self ):
        return 'error404page'
    
    def _generate404( self, url ):
        # Get the filename extension and create a 404 for it
        extension = urlParser.getExtension( url )
        domainPath = urlParser.getDomainPath( url )
        
        if not extension:
            rand_alnum_file = createRandAlNum( 8 )
            extension = ''
        else:
            rand_alnum_file = createRandAlNum( 8 ) + '.' + extension
            
        url404 = urlParser.urlJoin(  domainPath , rand_alnum_file )
        
        try:
            # I don't use the cache, because the URLs are random and the only thing that
            # useCache does is to fill up disk space
            response = self._urlOpener.GET( url404, useCache=False, grepResult=False )
        except w3afException, w3:
            raise w3afException('Exception while fetching a 404 page, error: ' + str(w3) )
        except w3afMustStopException, mse:
            # Someone else will raise this exception and handle it as expected
            # whenever the next call to GET is done
            raise w3afException('w3afMustStopException found by _generate404, someone else will handle it.')
        except Exception, e:
            raise w3afException('Unhandled exception while fetching a 404 page, error: ' + str(e) )
        
        # I don't want the random file name to affect the 404, so I replace it with a blank space
        response_body = self._get_clean_body( response )
        response.setBody(response_body)
        
        return response, extension
