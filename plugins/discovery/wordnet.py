'''
wordnet.py

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
from core.controllers.w3afException import w3afException

import core.data.parsers.urlParser as urlParser
from core.data.fuzzer.fuzzer import createMutants
import core.data.kb.knowledgeBase as kb
import re

# The pywordnet includes
#from extlib.pywordnet.wordnet import *
import extlib.pywordnet.wntools as wntools

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

class wordnet(baseDiscoveryPlugin):
    '''
    Use the wordnet lexical database to find new URLs.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # User defined parameters
        self._wordnet_results = 2     
        
    def discover(self, fuzzableRequest ):
        '''
        @parameter fuzzableRequest: A fuzzableRequest instance that contains
                                                    (among other things) the URL to test.
        '''
        self._fuzzableRequests = []
        self.is404 = kb.kb.getData( 'error404page', '404' )
        
        self._original_response = self._sendMutant( fuzzableRequest, analyze=False )
        
        for mutant in self._generate_mutants( fuzzableRequest ):
            targs = ( mutant, )
            self._tm.startFunction( target=self._check_existance, args=targs, ownerObj=self )
        self._tm.join( self )
        return self._fuzzableRequests
    
    def _check_existance( self, mutant ):
        '''
        Actually check if the mutated URL exists.
        @return: None, all important data is saved to self._fuzzableRequests
        '''
        response = self._sendMutant( mutant, analyze=False )
        if not self.is404( response ) and self._original_response.getBody() != response.getBody() :
            fuzzReqs = self._createFuzzableRequests( response )
            self._fuzzableRequests.extend( fuzzReqs )
    
    def _generate_mutants( self, fuzzableRequest ):
        '''
        Based on the fuzzable request, i'll search the wordnet database and generated
        A LOT of mutants.
        
        @return: A list of mutants.
        '''
        result = []
        result.extend( self._generate_fname( fuzzableRequest ) )
        result.extend( self._generate_qs( fuzzableRequest ) )
        return result
    
    def _generate_qs( self, fuzzableRequest ):
        '''
        Check the URL query string.
        @return: A list of mutants.
        '''     
        # The result
        result = []

        query_string = urlParser.getQueryString( fuzzableRequest.getURI() )
        for key in query_string.keys():
            wordnet_result = self._search_wn( query_string[key] )
            result.extend( self._generate_URL_from_result( key, wordnet_result, fuzzableRequest ) )
        return result

    def _add_words( self, word ):
        '''
        Fills a list with all the wordnet word types of a word and returns it.
        '''
        wn_word_list = []
        wntools_sources = [wntools.N, wntools.ADJ, wntools.V, wntools.ADV]
        
        for source in wntools_sources:
            try:
                wn_word_list.append( source[ word ] )
            except:
                pass
            
        return wn_word_list

    def _search_wn( self, word ):
        '''
        Search the wordnet for this word, based on user options.
        @return: A list of related words.
        '''
        results = {'syno':[], 'anto':[], 'hyper':[], 'hypo':[], 'mero':[], 'holo':[]}
        
        wn_word_list = self._add_words( word )
        wntools_types = [ wntools.ANTONYM, wntools.HYPERNYM, wntools.HYPONYM, 
                                    wntools.MEMBER_MERONYM, wntools.MEMBER_HOLONYM ]
        
        for word in wn_word_list:
            for sense in word:
                try:
                        
                    for pointer in sense.getPointers( wntools.ANTONYM ):
                        if not isinstance( pointer.target(), wntools.Synset ):
                            results['anto'].append( pointer.target().getWord() )
                        else:
                            for i in pointer.target():
                                results['anto'].append( i.getWord() )
                
                    for pointer in sense.getPointers( wntools.HYPERNYM ):
                        if not isinstance( pointer.target(), wntools.Synset ):
                            results['hyper'].append( pointer.target().getWord() )
                        else:
                            for i in pointer.target():
                                results['hyper'].append( i.getWord() )
                    
                    for pointer in sense.getPointers( wntools.HYPONYM ):
                        if not isinstance( pointer.target(), wntools.Synset ):
                            results['hypo'].append( pointer.target().getWord() )
                        else:
                            for i in pointer.target():
                                results['hypo'].append( i.getWord() )
                    
                    for pointer in sense.getPointers( wntools.MEMBER_MERONYM ):
                        if not isinstance( pointer.target(), wntools.Synset ):
                            results['mero'].append( pointer.target().getWord() )
                        else:
                            for i in pointer.target():
                                results['mero'].append( i.getWord() )
                    
                    for pointer in sense.getPointers( wntools.MEMBER_HOLONYM ):
                        if not isinstance( pointer.target(), wntools.Synset ):
                            results['holo'].append( pointer.target().getWord() )
                        else:
                            for i in pointer.target():
                                results['holo'].append( i.getWord() )
                
                except:
                    pass
        
        # Now I have a results map filled up with a lot of words.
        # The next step is to order each list by popularity, so I only send to the web
        # the most common words, not the strange and unused words.
        results = self._popularity_contest( results )
        
        resultList = []
        for key in results:
            strList = self._wn_words_to_str( results[key][: self._wordnet_results ] )
            resultList.extend( strList )
            
        return resultList
    
    def _popularity_contest( self, results ):
        '''
        @parameter results: The result map of the wordnet search.
        @return: The same result map, but each item is ordered by popularity
        '''
        def sort_function( i, j ):
            '''
            Compare the lengths of the objects.
            '''
            return cmp( len( i ) , len( j ) )
        
        for key in results:
            wordList = results[key]
            wordList.sort( sort_function )
            results[key] = wordList
            
        return results
    
    def _wn_words_to_str( self, wn_word_list ):
        tmp = []
        for i in wn_word_list:
            tmp.append( re.sub('\(.\.\)', '', str(i) ) )
                    
        results = [ x for x in tmp if not x.count( ' ' ) ]
        results = list( set( results ) )
        return results
    
    def _generate_fname( self, fuzzableRequest ):
        '''
        Check the URL filenames
        @return: A list mutants.
        '''
        url = fuzzableRequest.getURL()
        fname = self._get_filename( url )
        
        wordnet_result = self._search_wn( fname )
        result = self._generate_URL_from_result( None, wordnet_result, fuzzableRequest )
                
        return result
    
    def _get_filename( self, url ):
        '''
        @return: The filename, without the extension
        '''
        fname = urlParser.getFileName( url )
        splitted_fname = fname.split('.')
        name = ''
        if len(splitted_fname) != 0:
            name = splitted_fname[0]
        return name
            
    def _generate_URL_from_result( self, analyzed_variable, result_set, fuzzableRequest ):
        '''
        Based on the result, create the new URLs to test.
        @return: An URL list.
        '''
        if analyzed_variable == None:
            # The URL was analyzed
            url = fuzzableRequest.getURL()
            fname = urlParser.getFileName( url )
            dp = urlParser.getDomainPath( url )
            
            # The result
            result = []
            
            splitted_fname = fname.split('.')
            if len(splitted_fname) == 2:
                name = splitted_fname[0]
                extension = splitted_fname[1]
            else:
                name = splitted_fname[:-1]
                extension = 'html'
            
            for set_item in result_set:
                new_fname = fname.replace( name, set_item )
                frCopy = fuzzableRequest.copy()
                frCopy.setURL( urlParser.urlJoin( dp, new_fname ) )
                result.append( frCopy )
                
            return result
            
        else:
            mutants = createMutants( fuzzableRequest , result_set, \
                                                    fuzzableParamList=[analyzed_variable,] )
            return mutants
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Only use the first wnResults (wordnet results) from each category.'
        o1 = option('wnResults', self._wordnet_results, d1, 'integer')
        
        ol = optionList()
        ol.add(o1)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass

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
        This plugin finds new URL's using wordnet.
        
        An example is the best way to explain what this plugin does, let's suppose that the input
        for this plugin is:
            - http://a/index.asp?color=blue
    
        The plugin will search the wordnet database for words that are related with "blue", and return for
        example: "black" and "white". So the plugin requests this two URL's:
            - http://a/index.asp?color=black
            - http://a/index.asp?color=white
        
        If the response for those URL's is not a 404 error, and has not the same body content, then we have 
        found a new URI. The wordnet database is bundled with w3af, more information about wordnet can be
        found at : http://wordnet.princeton.edu/
        '''
