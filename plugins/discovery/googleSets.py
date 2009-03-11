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

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.data.searchEngines.googleSearchEngine import googleSearchEngine as google
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin

import core.data.parsers.urlParser as urlParser
from core.data.fuzzer.fuzzer import createMutants
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
        self._fuzzable_requests = []
        self._original_response = None
        
        # User variables
        self._min_input = 2
        self._set_results = 2
        
    def discover(self, fuzzableRequest ):
        '''
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        self._fuzzable_requests = []
        
        self._original_response = self._sendMutant( fuzzableRequest, analyze=False )
        
        for analyzed_variable, input_set in self._generate_input_set( fuzzableRequest ):
            
            domain_path = urlParser.getDomainPath( fuzzableRequest.getURL() )
            if ( domain_path, analyzed_variable, input_set ) not in self._analyzed:
                self._analyzed.append( ( domain_path, analyzed_variable, input_set ) )
                
                # Call verify
                targs = ( fuzzableRequest, analyzed_variable, input_set)
                self._tm.startFunction( target=self._verify, args=targs, ownerObj=self )
                
        self._tm.join( self )
        return self._fuzzable_requests
    
    def _verify( self, fuzzableRequest, analyzed_variable, input_set):
        '''
        Check if the set returned something meaningful, and add it to the self._fuzzable_requests
        list, that is going to be the return value of this plugin.
        '''
        # No key is used here because I fetch the results from the
        # google html page result.
        google_se = google( self._urlOpener )
        result_set = google_se.set( input_set )
        
        # Now i will cut the list using the user setting
        result_set = result_set[:self._set_results]
        mutant_list = self._generateURLsFromSet( analyzed_variable, result_set, fuzzableRequest )
        
        # Get the 404
        is_404 = kb.kb.getData( 'error404page', '404' )
        
        for mutant in mutant_list:
            response = self._sendMutant( mutant, analyze=False )
            
            if not is_404( response ) and \
            self._original_response.getBody() != response.getBody():
                fuzz_reqs = self._createFuzzableRequests( response )
                self._fuzzable_requests.extend( fuzz_reqs )
    
    def _generate_input_set( self, fuzzableRequest ):
        '''
        Based on the fuzzable request, i'll search the kb , try to find other URLs in
        the same path and create a set with the filenames of those URLs.
        
        Also analyze the parameters that are passed in the query string.
        
        @return: A list of tuples with ( analyzed_variable, result_set ). When analyzing the URL, the analyzed_variable is
        setted to None.
        '''
        result = []
        result.extend( self._generateISFname( fuzzableRequest ) )
        result.extend( self._generateISQs( fuzzableRequest ) )
        return result
    
    def _generateISQs( self, fuzzableRequest ):
        '''
        Check the URL query string.
        @return: A list of tuples with ( analyzed_variable, result_set ).
        '''     
        # The result
        result = []

        query_string = urlParser.getQueryString( fuzzableRequest.getURI() )
        input_set_map = {}
        for key in query_string.keys():
            input_set_map[ key ] = []
        
        uriList = kb.kb.getData( 'urls', 'uriList' )
        for uri in uriList:
            if fuzzableRequest.getURL() == urlParser.uri2url( uri ) and \
            urlParser.getQueryString( uri ).keys() == query_string.keys():
                # Both URL's have the same query string parameters
                for key in query_string.keys():
                    input_set_map[ key ].append( urlParser.getQueryString( uri )[ key ] )
        
        # Now I create the result, based on input_set_map
        for parameter_name in input_set_map:
            tmp = []
            for element_index in xrange(len(input_set_map[parameter_name])):
                tmp.extend( input_set_map[ key ][element_index] )
                tmp = list(set( tmp ) )
                
            result.append( ( key,  tmp) )
            
        return result

    def _generateISFname( self, fuzzableRequest ):
        '''
        Check the URL filenames
        @return: A list of tuples with ( analyzed_variable, result_set ). When analyzing the URL, the analyzed_variable is
        setted to None.
        '''
        url = fuzzableRequest.getURL()
        domain_path = urlParser.getDomainPath( url )
        
        # The result
        result = []
        other_names_in_path = []
        
        for url in kb.kb.getData( 'urls', 'urlList' ):
            if urlParser.getDomainPath( url ) == domain_path:
                # Both files are in the same path, they are related
                fname = urlParser.getFileName( url ).split('.')[0]
                other_names_in_path.append( fname )
        
        other_names_in_path = list( set(other_names_in_path) )
        
        if len(other_names_in_path) >= self._min_input:
            result.append( ( None, other_names_in_path ) )
                
        return result
    
    def _generateURLsFromSet( self, analyzed_variable, result_set, fuzzableRequest ):
        '''
        Based on the result, create the new URLs to test.
        @return: An URL list.
        '''
        if analyzed_variable == None:
            # The filename was analyzed
            url = fuzzableRequest.getURL()
            fname = urlParser.getFileName( url ).split('.')[0]
            dp = urlParser.getDomainPath( url )
            
            # The result
            result = []
            
            for set_item in result_set:
                new_fname = urlParser.getFileName( url.replace( fname, set_item ) )
                fr_copy = fuzzableRequest.copy()
                fr_copy.setURL( urlParser.urlJoin( dp, new_fname ) )
                result.append( fr_copy )
                
            return result
            
        else:
            # We are fuzzing a query string parameter.
            mutants = createMutants( fuzzableRequest , result_set,
                                                    fuzzableParamList=[analyzed_variable,] )
            return mutants
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Only try to create a set if the plugin can provide minInput inputs to the query.'
        o1 = option('minInput', self._min_input, d1, 'integer')
        
        d2 = 'Only use the first setResults results of the query.'
        o2 = option('setResults', self._set_results, d2, 'integer')
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        return ol
    
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._min_input = optionsMap['minInput'].getValue()
        self._set_results = optionsMap['setResults'].getValue()
                
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
