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

from core.data.fuzzer.fuzzer import createMutants
from core.controllers.coreHelpers.fingerprint_404 import is_404

from core.data.nltk_wrapper.nltk_wrapper import wn

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
        
        self._original_response = self._sendMutant( fuzzableRequest, analyze=False )
        
        for mutant in self._generate_mutants( fuzzableRequest ):
            #   Send the requests using threads:
            targs = ( mutant, )
            self._tm.startFunction( target=self._check_existance, args=targs, ownerObj=self )
            
        # Wait for all threads to finish
        self._tm.join( self )
        return self._fuzzableRequests
    
    def _check_existance( self, mutant ):
        '''
        Actually check if the mutated URL exists.
        @return: None, all important data is saved to self._fuzzableRequests
        '''
        response = self._sendMutant( mutant, analyze=False )
        if not is_404( response ) and self._original_response.getBody() != response.getBody() :
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

        query_string = fuzzableRequest.getURI().getQueryString()
        for parameter_name in query_string:
            # this for loop was added to address the repeated parameter name issue
            for element_index in xrange(len(query_string[parameter_name])):
                wordnet_result = self._search_wn( query_string[parameter_name][element_index] )
                result.extend( self._generate_URL_from_result( parameter_name, element_index, wordnet_result, fuzzableRequest ) )
        return result

    def _search_wn( self, word ):
        '''
        Search the wordnet for this word, based on user options.
        @return: A list of related words.
        
        >> wn.synsets('blue')[0].hypernyms()
        [Synset('chromatic_color.n.01')]
        >> wn.synsets('blue')[0].hypernyms()[0].hyponyms()
        [Synset('orange.n.02'), Synset('brown.n.01'), Synset('green.n.01'), 
         Synset('salmon.n.04'), Synset('red.n.01'), Synset('blue.n.01'), Synset('blond.n.02'), 
         Synset('purple.n.01'), Synset('olive.n.05'), Synset('yellow.n.01'), Synset('pink.n.01'), 
         Synset('pastel.n.01'), Synset('complementary_color.n.01')]
        '''
        result = []
        
        # Now the magic that gets me a lot of results:
        try:
            result.extend( wn.synsets(word)[0].hypernyms()[0].hyponyms() )
        except:
            pass
        
        synset_list = wn.synsets( word )
        
        for synset in synset_list:
            
            # first I add the synsec as it is:
            result.append( synset )
            
            # Now some variations...
            result.extend( synset.hypernyms() )
            result.extend( synset.hyponyms() )
            result.extend( synset.member_holonyms() )
            result.extend( synset.lemmas[0].antonyms() )

        # Now I have a results list filled up with a lot of words, the problem is that
        # this words are really Synset objects, so I'll transform them to strings:
        result = [ i.name.split('.')[0] for i in result]
        
        # Another problem with Synsets is that the name is "underscore separated"
        # so, for example:
        # "big dog" is "big_dog"
        result = [ i.replace('_', ' ') for i in result]
        
        # Now I make a "uniq"
        result = list(set(result))
        if word in result: result.remove(word)
        
        # The next step is to order each list by popularity, so I only send to the web
        # the most common words, not the strange and unused words.
        result = self._popularity_contest( result )
        
        # left here for debugging!
        #print word, result
        
        return result
    
    def _popularity_contest( self, result ):
        '''
        @parameter results: The result map of the wordnet search.
        @return: The same result map, but each item is ordered by popularity
        '''
        def sort_function( i, j ):
            '''
            Compare the lengths of the objects.
            '''
            return cmp( len( i ) , len( j ) )
        
        result.sort( sort_function )
            
        return result
    
    def _generate_fname( self, fuzzableRequest ):
        '''
        Check the URL filenames
        @return: A list mutants.
        '''
        url = fuzzableRequest.getURL()
        fname = self._get_filename( url )
        
        wordnet_result = self._search_wn( fname )
        result = self._generate_URL_from_result( None, None, wordnet_result, fuzzableRequest )
                
        return result
    
    def _get_filename( self, url ):
        '''
        @return: The filename, without the extension
        '''
        fname = url.getFileName()
        splitted_fname = fname.split('.')
        name = ''
        if len(splitted_fname) != 0:
            name = splitted_fname[0]
        return name
            
    def _generate_URL_from_result( self, analyzed_variable, element_index, result_set, fuzzableRequest ):
        '''
        Based on the result, create the new URLs to test.
        
        @parameter analyzed_variable: The parameter name that is being analyzed
        @parameter element_index: 0 in most cases, >0 if we have repeated parameter names
        @parameter result_set: The set of results that wordnet gave use
        @parameter fuzzableRequest: The fuzzable request that we got as input in the first place.
        
        @return: An URL list.
        '''
        if analyzed_variable is None:
            # The URL was analyzed
            url = fuzzableRequest.getURL()
            fname = url.getFileName()
            domain_path = url.getDomainPath()
            
            # The result
            result = []
            
            splitted_fname = fname.split('.')
            if len(splitted_fname) == 2:
                name = splitted_fname[0]
                extension = splitted_fname[1]
            else:
                name = '.'.join(splitted_fname[:-1])
                extension = 'html'
            
            for set_item in result_set:
                new_fname = fname.replace( name, set_item )
                frCopy = fuzzableRequest.copy()
                frCopy.setURL( domain_path.urlJoin( new_fname ) )
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
        This plugin finds new URL's using wn.
        
        An example is the best way to explain what this plugin does, let's suppose that the input
        for this plugin is:
            - http://a/index.asp?color=blue
    
        The plugin will search the wordnet database for words that are related with "blue", and return for
        example: "black" and "white". So the plugin requests this two URL's:
            - http://a/index.asp?color=black
            - http://a/index.asp?color=white
        
        If the response for those URL's is not a 404 error, and has not the same body content, then we have 
        found a new URI. The wordnet database is bundled with w3af, more information about wordnet can be
        found at : http://wn.princeton.edu/
        '''
