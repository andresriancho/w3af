'''
error404page.py

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
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.kb.knowledgeBase as kb
import core.data.parsers.urlParser as urlParser
from core.data.fuzzer.fuzzer import *
import re
from core.controllers.w3afException import w3afRunOnce

class error404page(baseDiscoveryPlugin):
    '''
    Read the 404 page returned by the server.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # User configured parameters
        self._always404 = []
        self._404exceptions = []
        
        # Note that \ are escaped first !
        self._metachars = ['\\', '.', '^', '$', '*', '+', '?', '{', '[', ']', \
        '|', '(', ')','..','\\d','\\D','\\s','\\S','\\w','\\W',\
        '\\A', '\\Z', '\\b','\\B']
        self._404dirRegexMap = {}
        
        # This is gooood! It will put the function in a place that's available for all.
        kb.kb.save( self, '404', self.is404 )
        
        # Only report once
        self._reported = False

    def discover(self, fuzzableRequest ):
        '''
        Get a page that doesnt exist and generate the is404 function
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        domainPath = urlParser.getDomainPath( fuzzableRequest.getURL() )
        if domainPath not in self._404dirRegexMap.keys():
            try:
                self._createRegex( fuzzableRequest )
            except:
                pass
        
        return []
    
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
        
        if domainPath in self._always404:
            return True
        elif domainPath in self._404exceptions:
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
    
    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/ui/userInterface.dtd
        
        @return: XML with the plugin options.
        ''' 
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
            <Option name="404exceptions">\
                <default>'+','.join(self._404exceptions)+'</default>\
                <desc>A comma separated list that determines what URLs will NEVER be detected as 404 pages.</desc>\
                <type>list</type>\
            </Option>\
            <Option name="always404">\
                <default>'+','.join(self._always404)+'</default>\
                <desc>A comma separated list that determines what URLs will ALWAYS be detected as 404 pages.</desc>\
                <type>list</type>\
            </Option>\
        </OptionList>\
        '

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
        @parameter optionsMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._404exceptions = optionsMap['404exceptions']
        self._always404 = optionsMap['always404']

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin generates a regular expression that identifies 404 error pages. The regular expression
        is generated for every new directory that is tested.

        Other plugins can use this knowledge to identify 404 pages.
        '''
