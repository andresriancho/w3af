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
from core.controllers.w3afException import w3afException
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.parsers.urlParser as urlParser
from core.data.fuzzer.fuzzer import *
import core.data.kb.knowledgeBase as kb
import re

# The pywordnet includes
from extlib.pywordnet.wordnet import *
from extlib.pywordnet.wntools import *

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

class wordnet(baseDiscoveryPlugin):
    '''
    Use the wordnet lexical database to find new URLs.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    '''
    Example:
    
    input:
    http://a/index.asp?color=blue
    http://a/index.asp?color=red
    
    toTest 4 existance (returned by google set):
    http://a/index.asp?color=black
    http://a/index.asp?color=white
    ...
    ...
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # User variables
        self._wnResults = 2     
        
    def discover(self, fuzzableRequest ):
        '''
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        self._fuzzableRequests = []
        self.is404 = kb.kb.getData( 'error404page', '404' )
        
        self._originalResponse = self._sendMutant( fuzzableRequest, analyze=False )
        
        for mutant in self._generateMutants( fuzzableRequest ):
            targs = ( mutant, )
            self._tm.startFunction( target=self._verify, args=targs, ownerObj=self )
        self._tm.join( self )
        return self._fuzzableRequests
    
    def _verify( self, mutant ):
        
        response = self._sendMutant( mutant, analyze=False )
        if not self.is404( response ) and self._originalResponse.getBody() != response.getBody() :
            fuzzReqs = self._createFuzzableRequests( response )
            self._fuzzableRequests.extend( fuzzReqs )
    
    def _generateMutants( self, fuzzableRequest ):
        '''
        Based on the fuzzable request, i'll search the wordnet database and generated
        A LOT of mutants.
        
        @return: A list of mutants.
        '''
        result = []
        result.extend( self._generateFname( fuzzableRequest ) )
        result.extend( self._generateQs( fuzzableRequest ) )
        return result
    
    def _generateQs( self, fuzzableRequest ):
        '''
        Check the URL query string.
        @return: A list of mutants.
        '''     
        # The result
        result = []

        qs = urlParser.getQueryString( fuzzableRequest.getURI() )
        for key in qs.keys():
            wordnetResult = self._searchWN( qs[key] )
            result.extend( self._generateURLFromResult( key, wordnetResult, fuzzableRequest ) )
        return result

    def _addWords( self, word ):
        '''
        Fills a list with all the wordnet word types of a word and returns it.
        '''
        wnWordList = []
        try:
            wnWordList.append( N[ word ] )
        except:
            pass
            
        try:
            wnWordList.append( ADJ[ word ] )
        except:
            pass
            
        try:
            wnWordList.append( V[ word ] )
        except:
            pass
            
        try:
            wnWordList.append( ADV[ word ] )
        except:
            pass
        
        return wnWordList

    def _searchWN( self, word ):
        '''
        Search the wordnet for this word, based on user options.
        @return: A list of related words.
        '''
        results = {'syno':[],'anto':[],'hyper':[],'hypo':[],'mero':[],'holo':[]}
        
        wnWordList = self._addWords( word )
        
        for word in wnWordList:
            for sense in word:
                
                # the biggest try/except in the history of w3af ! :P
                try:
                    
                    for pointer in sense.getPointers( ANTONYM ):
                        if not isinstance( pointer.target(), Synset ):
                            results['anto'].append( pointer.target().getWord() )
                        else:
                            for i in pointer.target():
                                results['anto'].append( i.getWord() )
                
                    for pointer in sense.getPointers( HYPERNYM ):
                        if not isinstance( pointer.target(), Synset ):
                            results['hyper'].append( pointer.target().getWord() )
                        else:
                            for i in pointer.target():
                                results['hyper'].append( i.getWord() )
                    
                    for pointer in sense.getPointers( HYPONYM ):
                        if not isinstance( pointer.target(), Synset ):
                            results['hypo'].append( pointer.target().getWord() )
                        else:
                            for i in pointer.target():
                                results['hypo'].append( i.getWord() )
                    
                    for pointer in sense.getPointers( MEMBER_MERONYM ):
                        if not isinstance( pointer.target(), Synset ):
                            results['mero'].append( pointer.target().getWord() )
                        else:
                            for i in pointer.target():
                                results['mero'].append( i.getWord() )
                    
                    for pointer in sense.getPointers( MEMBER_HOLONYM ):
                        if not isinstance( pointer.target(), Synset ):
                            results['holo'].append( pointer.target().getWord() )
                        else:
                            for i in pointer.target():
                                results['holo'].append( i.getWord() )
                
                except:
                    pass
        
        # Now I have a results map filled up with a lot of words.
        # The next step is to order each list by popularity, so I only send to the web
        # the most common words, not the strange and unused words.
        results = self._popularityContest( results )
        
        resultList = []
        for key in results:
            strList = self._wnWordsToStr( results[key][: self._wnResults ] )
            resultList.extend( strList )
            
        return resultList
    
    def _popularityContest( self, results ):
        '''
        @parameter results: The result map of the wordnet search.
        @return: The same result map, but each item is ordered by popularity
        '''
        def sortFunction( x, y ):
            return cmp( len( x ) , len( y ) )
        
        for key in results:
            wordList = results[key]
            wordList.sort( sortFunction )
            results[key] = wordList
            
        return results
    
    def _wnWordsToStr( self, wnWordList ):
        tmp = []
        for i in wnWordList:
            tmp.append( re.sub('\(.\.\)','', str(i) ) )
                    
        results = [ x for x in tmp if not x.count( ' ' ) ]
        results = list( set( results ) )
        return results
    
    def _generateFname( self, fuzzableRequest ):
        '''
        Check the URL filenames
        @return: A list mutants.
        '''
        url = fuzzableRequest.getURL()
        fname = self._getFilename( url )
        dp = urlParser.getDomainPath( url )
        
        wordnetResult = self._searchWN( fname )
        result = self._generateURLFromResult( None, wordnetResult, fuzzableRequest )
                
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
            
    def _generateURLFromResult( self, analyzedVariable, resultSet, fuzzableRequest ):
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
        return str(self.getOptions())
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Only use the first wnResults (wordnet results) from each category.'
        o1 = option('wnResults', self._wnResults, d1, 'integer')
        
        ol = optionList()
        ol.add(o1)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
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
