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
        
        # This is gooood! It will put the function in a place that's available for all.
        kb.kb.save( 'error404page', '404', self.is_404 )

        # Only report once
        self._reported = False
        self._already_analyzed = False
        self._404_body = ''

    def is_404(self, http_response):
        '''
        All of my previous versions of is_404 were very complex and tried to struggle with all
        possible cases. The truth is that in most "strange" cases I was failing miserably, so now
        I changed my 404 detection once again, but keeping it as simple as possible.
        
        Also, and because I was trying to cover ALL CASES, I was performing a lot of
        requests in order to cover them, which in most situations was unnecesary.
        
        So now I go for a much simple approach:
            1- Cover the simplest case of all using only 1 HTTP request
            2- Give the users the power to configure the 404 detection by setting a string that
            identifies the 404 response (in case we are missing it for some reason in case #1)
        
        @parameter http_response: The HTTP response which we want to know if it is a 404 or not.
        '''
        #
        #   First we handle the user configured exceptions:
        #
        domain_path = urlParser.getDomainPath(http_response.getURL())
        if domain_path in cf.cf.getData('always404'):
            return True
        elif domain_path in cf.cf.getData('never404'):
            return False        
        
        #
        #   This is the most simple case, we don't even have to think about this.
        #
        #   If there is some custom website that always returns 404 codes, then we are
        #   fucked, but this is open source, and the pentester working on that site can modify
        #   these lines.
        #
        if http_response.getCode() == 404 or http_response.getCode() == 401:
            return True
            
        #
        #   The user configured setting. "If this string is in the response, then it is a 404"
        #
        if cf.cf.getData('never404') and cf.cf.getData('never404') in http_response:
            return True
            
        if not self._already_analyzed:
            # Generate a 404 and save it
            self._404_body = self._generate404( http_response.getURL() )
            self._already_analyzed = True
            
        # self._404_body was already cleaned inside self._generate404
        # so we need to clean this one.
        html_body = self._get_clean_body( http_response )
        
        ratio = relative_distance( self._404_body, html_body )
        if ratio > IS_EQUAL_RATIO:
            msg = '"' + http_response.getURL() + '" is a 404.' + str(ratio) + ' > '
            msg += str(IS_EQUAL_RATIO)
            om.out.debug( msg )
            return True
        else:
            return False
            
    def _generate404( self, url ):
        '''
        Based on a URL, request something that we know is going to be a 404, 
        and return the body.
        '''
        # Get the filename extension and create a 404 for it
        extension = urlParser.getExtension( url )
        domain_path = urlParser.getDomainPath( url )
        
        if not extension:
            rand_alnum_file = createRandAlNum( 8 )
            extension = ''
        else:
            rand_alnum_file = createRandAlNum( 8 ) + '.' + extension
            
        url404 = urlParser.urlJoin(  domain_path , rand_alnum_file )
        
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
        
        
    #
    #
    #       Some helper functions
    #
    #
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
        
    def getName( self ):
        return 'error404page'
        
