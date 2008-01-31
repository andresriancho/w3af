'''
googleSets.py

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
from core.controllers.w3afException import w3afException
from core.data.searchEngines.google import google as google
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.parsers.urlParser as urlParser
from core.data.fuzzer.fuzzer import *
import core.data.kb.knowledgeBase as kb

class googleSets(baseDiscoveryPlugin):
    '''
    Use Google sets to get related words from an URI and test them to find new URLs.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        # Internal variables
        self._analyzed = []     
        
        # User variables
        self._minInput = 2
        self._setResults = 2
        
    def discover(self, fuzzableRequest ):
        '''
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        self._fuzzableRequests = []
        self.is404 = kb.kb.getData( 'error404page', '404' )
        self._google = google( self._urlOpener )    # No key is used here
        
        self._originalResponse = self._sendMutant( fuzzableRequest, analyze=False )
        
        for analyzedVariable, inputSet in self._generateInputSet( fuzzableRequest ):
            if ( fuzzableRequest.getURL(), analyzedVariable, inputSet ) not in self._analyzed:
                self._analyzed.append( ( fuzzableRequest.getURL(), analyzedVariable, inputSet ) )
                targs = ( fuzzableRequest, analyzedVariable, inputSet)
                self._tm.startFunction( target=self._verify, args=targs, ownerObj=self )        
        self._tm.join( self )
        return self._fuzzableRequests
    
    def _verify( self, fuzzableRequest, analyzedVariable, inputSet):
        
        resultSet = self._google.set( inputSet )
        # Now i will cut the list using the user setting
        resultSet = resultSet[:self._setResults]
        mutantList = self._generateURLsFromSet( analyzedVariable, resultSet, fuzzableRequest )
        
        for m in mutantList:
            response = self._sendMutant( m, analyze=False )
            if not self.is404( response ) and self._originalResponse.getBody() != response.getBody() :
                fuzzReqs = self._createFuzzableRequests( response )
                self._fuzzableRequests.extend( fuzzReqs )
    
    def _generateInputSet( self, fuzzableRequest ):
        '''
        Based on the fuzzable request, i'll search the kb , try to find other URLs in
        the same path and create a set with the filenames of those URLs.
        
        Also analyze the parameters that are passed in the query string.
        
        @return: A list of tuples with ( analyzedVariable, resultSet ). When analyzing the URL, the analyzedVariable is
        setted to None.
        '''
        result = []
        result.extend( self._generateISFname( fuzzableRequest ) )
        result.extend( self._generateISQs( fuzzableRequest ) )
        return result
    
    def _generateISQs( self, fuzzableRequest ):
        '''
        Check the URL query string.
        @return: A list of tuples with ( analyzedVariable, resultSet ).
        '''     
        # The result
        result = []

        qs = urlParser.getQueryString( fuzzableRequest.getURI() )
        inputSetMap = {}
        for key in qs.keys():
            inputSetMap[ key ] = []
        
        uriList = kb.kb.getData( 'urls', 'uriList' )
        for uri in uriList:
            if fuzzableRequest.getURL() == urlParser.uri2url( uri ) and \
            urlParser.getQueryString( uri ).keys() == qs.keys():
                # Both URL's have the same query string parameters
                for key in qs.keys():
                    inputSetMap[ key ].append( urlParser.getQueryString( uri )[ key ] )
        
        # Now I create the result, based on inputSetMap
        for key in inputSetMap:
            result.append( ( key, list(set(inputSetMap[ key ] ) ) ) )
            
        return result

    
    def _generateISFname( self, fuzzableRequest ):
        '''
        Check the URL filenames
        @return: A list of tuples with ( analyzedVariable, resultSet ). When analyzing the URL, the analyzedVariable is
        setted to None.
        '''
        url = fuzzableRequest.getURL()
        fname = self._getFilename( url )
        dp = urlParser.getDomainPath( url )
        
        # The result
        result = []
        otherNamesInPath = []
        
        urlList = kb.kb.getData( 'urls', 'urlList' )
        for url in urlList:
            if urlParser.getDomainPath( url ) == dp:
                # Both files are in the same path
                otherNamesInPath.append( self._getFilename( url ) )
        
        if len(otherNamesInPath) >= self._minInput:
            result.append( ( None, otherNamesInPath ) )
                
        return result
    
    def _getFilename( self, url ):
        '''
        @return: The filename, without the extension
        '''
        fname = urlParser.getFileName( url )
        splittedFname = fname.split('.')
        name = ''
        if len(splittedFname) != 0:
            name = splittedFname[0]
        return name
            
    def _generateURLsFromSet( self, analyzedVariable, resultSet, fuzzableRequest ):
        '''
        Based on the result, create the new URLs to test.
        @return: An URL list.
        '''
        if analyzedVariable == None:
            # The URL was analyzed
            url = fuzzableRequest.getURL()
            fname = urlParser.getFileName( url )
            dp = urlParser.getDomainPath( url )
            
            # The result
            result = []
            
            splittedFname = fname.split('.')
            if len(splittedFname) == 2:
                name = splittedFname[0]
                extension = splittedFname[1]
            else:
                name = splittedFname[0]
                extension = 'html'
            
            for setItem in resultSet:
                newFname = url.replace( name, setItem )
                frCopy = fuzzableRequest.copy()
                frCopy.setURL( urlParser.urlJoin( dp, newFname ) )
                result.append( frCopy )
                
            return result
            
        else:
            mutants = createMutants( fuzzableRequest , resultSet, fuzzableParamList=[analyzedVariable,] )
            return mutants
        
    
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
            <Option name="minInput">\
                <default>'+str(self._minInput)+'</default>\
                <desc>Only try to create a set if the plugin can provide minInput inputs to the query.</desc>\
                <type>integer</type>\
                <help></help>\
            </Option>\
            <Option name="setResults">\
                <default>'+str(self._setResults)+'</default>\
                <desc>Only use the first setResults results of the query.</desc>\
                <type>integer</type>\
                <help></help>\
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
        self._minInput = optionsMap['minInput']
        self._setResults = optionsMap['setResults']
                
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
        This plugin finds new URL's using google sets.
        
        Two configurable parameters exist:
            - resultLimit
            - setResults
        
        An example is the best way to explain what this plugin does, let's suppose that the input
        for this plugin is:
            - http://a/index.asp?color=blue
            - http://a/index.asp?color=red
    
        The plugin will search google sets for a set that contains the words "blue" and "red", and the result
        will be: "black" and "white". So the plugin requests this two URL's:
            - http://a/index.asp?color=black
            - http://a/index.asp?color=white
        
        If the response for those URL's is not a 404 error, and has not the same body content, then we have 
        found a new URI.
        '''
