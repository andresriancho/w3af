'''
digitSum.py

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
import core.data.parsers.urlParser as urlParser
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.kb.knowledgeBase as kb
from core.data.getResponseType import *
from core.controllers.w3afException import w3afException
import re

class digitSum(baseDiscoveryPlugin):
    '''
    Take an URL with a number ( index2.asp ) and try to find related files ( index1.asp , index3.asp ).
    @author: Andres Riancho ( andres.riancho@gmail.com )  
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._alreadyVisited = []
        self._firstTime = True
        
        # This is for the Referer
        self._headers = {}
        
        # User options
        self._fuzzImages = False
        self._maxDigitSections = 3
        
    def discover(self, fuzzableRequest ):
        '''
        Searches for new Url's by adding and substracting numbers to the url and the parameters.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        self._fuzzableRequests = []
            
        url = fuzzableRequest.getURL()
        self._headers = {'Referer':url}
        
        if self._firstTime:
            self._firstTime = False
            self.is404 = kb.kb.getData( 'error404page', '404' )
        
        om.out.debug('digitSum is testing ' + fuzzableRequest.getURL() )
        self._ores = originalResponse = self._urlOpener.GET( fuzzableRequest.getURL(), useCache=True, headers=self._headers )
        
        if isTextOrHtml( originalResponse.getHeaders() ) or self._fuzzImages:
            
            for fr in self._mangleDigits( fuzzableRequest ):
                if fr.getURL() not in self._alreadyVisited:
                    self._alreadyVisited.append( fr.getURI() )
                    
                    targs = ( fr, )
                    self._tm.startFunction( target=self._doRequest, args=targs , ownerObj=self )
            
            self._tm.join( self )
            # I add myself so the next call to this plugin wont find me ...
            # Example: index1.html ---> index2.html --!!--> index1.html
            self._alreadyVisited.append( fuzzableRequest.getURI() )
                
        return self._fuzzableRequests

    def _doRequest( self, fr ):
        try:
            response = self._urlOpener.GET( fr.getURI(), useCache=True, headers=self._headers )
        except KeyboardInterrupt,e:
            raise e
        else:
            if not self.is404( response ) and response.getBody() != self._ores.getBody():
                self._fuzzableRequests.append( fr )
                om.out.debug('digitSum plugin found new URI: ' + fr.getURI() )
    
    def _mangleDigits(self, fuzzableRequest):
        '''
        Mangle those digits.
        @param fuzzableRequest: The original fuzzableRequest
        @return: A list of fuzzableRequests.
        '''
        res = []
        # First i'll mangle the digits in the URL file
        filename = urlParser.getFileName( fuzzableRequest.getURL() )
        dp = urlParser.getDomainPath( fuzzableRequest.getURL() )
        for fname in self._doCombinations( filename ):
            copiedFr = fuzzableRequest.copy()
            copiedFr.setURL( dp + fname)
            res.append( copiedFr )
        
        # Now i'll mangle the query string variables
        if fuzzableRequest.getMethod() == 'GET':
            for parameter in fuzzableRequest.getDc().keys():
                for moddedVariable in self._doCombinations( fuzzableRequest.getDc()[ parameter ] ):
                    copiedFr = fuzzableRequest.copy()
                    newDc = copiedFr.getDc()
                    newDc[ parameter ] = moddedVariable
                    copiedFr.setDc( newDc )
                    res.append( copiedFr )
                    
        return res
        
    def _doCombinations( self, aString ):
        '''
        Example:
            - input: 'abc123'
            - output: ['abc122','abc124']
        
        Example:
            - input: 'abc123def01'
            - output: ['abc122def01','abc124def01','abc123def00','abc123def02']
        
        '''
        res = []
        splitted = self._findDigits( aString )
        if len( splitted ) < 2 * self._maxDigitSections:
            for i in xrange( len( splitted ) ):
                if splitted[ i ].isdigit():
                    splitted[ i ] = str( int(splitted[ i ]) + 1 )
                    res.append( ''.join(splitted) )
                    splitted[ i ] = str( int(splitted[ i ]) - 2 )
                    res.append( ''.join(splitted) )
                    splitted[ i ] = str( int(splitted[ i ]) + 1 )
        return res
                
    def _findDigits( self, aString ):
        '''
        Finds digits in a string and returns a list with string sections.
        For example:
            - input: 'foob45'
            - output: ['foo', '45']
            
        Another example:
            - input: 'f001bar112'
            - output: ['f', '00', 'bar', '112']
        
        @return: A list of strings.
        '''
        
        # regexes are soooooooooooooo cool !
        return [ x for x in re.split( r'(\d+)', aString ) if x != '' ]
        
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
            <Option name="fuzzImages">\
                <default>'+str(self._fuzzImages)+'</default>\
                <desc>Apply URL fuzzing to all URLs, including images, videos, zip, etc.</desc>\
                <type>boolean</type>\
                <help>It\'s safe to leave this option as the default.</help>\
            </Option>\
            <Option name="maxDigitSections">\
                <default>'+str(self._maxDigitSections)+'</default>\
                <desc>Set the top number of sections to fuzz</desc>\
                <type>boolean</type>\
                <help>It\'s safe to leave this option as the default. For example, with maxDigitSections = 1, this string wont be fuzzed:\
                abc123def234 ; but this one will abc23ldd.</help>\
            </Option>\
        </OptionList>\
        '

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._fuzzImages = optionsMap['fuzzImages']
        self._maxDigitSections = optionsMap['maxDigitSections']
    
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return ['discovery.error404page']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin tries to find new URL's by changing the numbers that are present on it.
        
        Two configurable parameters exist:
            - fuzzImages
            - maxDigitSections
        
        An example will clarify what this plugin does, let's suppose that the input for this plugin is:
            - http://a/index1.asp
            
        This plugin will request:
            - http://a/index0.asp
            - http://a/index2.asp
            
        If the response for the newly generated URL's ain't a 404 error, then the new URL is a valid one that
        can contain more information and injection points.      
        '''
