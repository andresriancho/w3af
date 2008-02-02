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
from core.data.fuzzer.fuzzer import *
import re

class fingerprint404Page:
    '''
    Read the 404 page returned by the server.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self, uriOpener):
        self._urlOpener =  uriOpener
        
        # Note that \ are escaped first !
        self._metachars = ['\\', '.', '^', '$', '*', '+', '?', '{', '[', ']', \
        '|', '(', ')','..','\\d','\\D','\\s','\\S','\\w','\\W',\
        '\\A', '\\Z', '\\b','\\B']
        self._404dirRegexMap = {}
        
        # This is gooood! It will put the function in a place that's available for all.
        kb.kb.save( 'error404page', '404', self.is404 )
        
        # Only report once
        self._reported = False

    def  _createRegex( self, fuzzableRequest ):
        '''
        Creates the regular expression and saves it to the kb.
        '''
        domainPath = urlParser.getDomainPath( fuzzableRequest.getURL() )
        try:
            response, randAlNumFile = self._generate404( fuzzableRequest.getURL() )
        except Exception, e:
            om.out.debug('Something went wrong with the 404 regex creation...')
            raise e
        else:
            if response.getCode() != 404 and not self._reported:
                # Not using 404 in error pages
                om.out.information('Server uses ' + str(response.getCode()) + ' instead of HTTP 404 error code. ')
                self._reported = True
            
            # Escape special characters
            is404regexStr = response.getBody()
            for c in self._metachars:
                is404regexStr = is404regexStr.replace( c, '\\'+c )
            
            # For some reason I dont want to know about, ' ' (spaces) must be escaped also
            is404regexStr = is404regexStr.replace( ' ', '\\ ' )
            
            # If the 404 error showed the URL I requested, replace that with a ".*?"
            randAlNumFile = randAlNumFile.replace( '.', '\\.' )
            is404regexStr = is404regexStr.replace( randAlNumFile, '.*?' )
            is404regexStr = '^' + is404regexStr + '$'
            
            om.out.debug('The is404 regex for "'+domainPath+'" is : "'+is404regexStr+'".')
            
            self._404dirRegexMap[ domainPath ] = re.compile( is404regexStr )
            kb.kb.save( self, '404', self.is404 )
    
    def is404( self, httpResponse ):
        domainPath = urlParser.getDomainPath( httpResponse.getURL() )
        
        if domainPath in cf.cf.getData('always404'):
            return True
        elif domainPath in cf.cf.getData('404exceptions'):
            return False
        elif domainPath in self._404dirRegexMap.keys():
            # Get the regex string from the map
            is404regex = self._404dirRegexMap[ domainPath ]
            
            # Do the matching.
            # I'm a regex dummy...
            if is404regex.match( httpResponse.getBody() ) or is404regex.match( httpResponse.getBody(), re.DOTALL ):
                om.out.debug('The URL: ' + httpResponse.getURL() + ' was identified as a 404.')
                return True
            else:
                om.out.debug('The URL: ' + httpResponse.getURL() + ' is NOT a 404.')
                return False
        
        else:
            # Not generated the is404regexStr for this directory yet
            # generate it and call is404 again.
            try:
                self._createRegex( httpResponse )
            except:
                # hmmm....
                # BUGBUG! When the regex creation fails, the pages are NEVER a 404.... hmmm...
                return False
            else:
                return self.is404( httpResponse )
    
    def getName( self ):
        return 'error404page'
    
    def _generate404( self, url ):
        randAlNumFile = createRandAlNum( 11 ) + '.html'
        url404 = urlParser.urlJoin(  url , randAlNumFile )
        try:
            response = self._urlOpener.GET( url404, useCache=True, grepResult=False )
        except w3afException, w3:
            raise w3afException('Exception while fetching a 404 page, error: ' + str(w3) )
        except Exception, e:
            raise w3afException('Unhandled exception while fetching a 404 page, error: ' + str(e) )
            
        return response, randAlNumFile
