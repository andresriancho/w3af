'''
lang.py

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
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
import core.data.kb.knowledgeBase as kb

class lang(baseGrepPlugin):
    '''
    Read N pages and determines the language the site is written in.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        # Internal variables
        self._exec = True
        
        # Some constants
        self._prepositions = {}
        
        self._prepositions[ 'en' ] = ['aboard','about','above','absent','across','after','against','along','alongside','amid','amidst',\
        'among','amongst','around','as','astride','at','atop','before','behind','below','beneath','beside','besides',\
        'between','beyond','but','by','despite','down','during','except','following','for','from','in','inside','into','like','mid','minus','near',\
        'nearest','notwithstanding','of','off','on','onto','opposite','out','outside','over','past','re','round','save',\
        'since','than','through','throughout','till','to','toward','towards','under','underneath','unlike','until','up',\
        'upon','via','with','within','without']

        
        # The 'a' preposition was removed, cause its also used in english
        self._prepositions[ 'es' ] = ['ante', 'bajo', 'cabe', 'con' , 'contra' , 'de', \
        'desde', 'en', 'entre', 'hacia', 'hasta', 'para', 'por' , 'segun', 'si', 'so', 'sobre', 'tras']
        
    def _testResponse(self, request, response):
        '''
        Get the page indicated by the fuzzableRequest and determine the language using the preposition list.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        self.is404 = kb.kb.getData( 'error404page', '404' )
        if self._exec and not self.is404( response ):
            kb.kb.save( self, 'lang', 'unknown' )
            
            splittedBody = response.getBody().split(' ')
            
            # Init the count map
            numberOfmatches = {}
            for lang in self._prepositions.keys():
                numberOfmatches[ lang ] = 0
            
            # Count prepositions
            for lang in self._prepositions.keys():
                for preposition in self._prepositions[ lang ]:
                    if preposition in splittedBody:
                        om.out.debug('Found preposition: ' + preposition)
                        numberOfmatches[ lang ] += 1
                        
            # Determine who is the winner
            def sortfunc(x,y):
                return cmp(y[1],x[1])
                
            items = numberOfmatches.items()
            items.sort( sortfunc )
            
            if items[0][1] > items[1][1] * 2:
                
                # This if was added so no duplicated messages are printed
                # to the user, when w3af runs with multithreading.
                if kb.kb.getData( 'lang', 'lang' ) == 'unknown':
                    om.out.information('The page language is: '+ items[0][0] )
                    kb.kb.save( self, 'lang', items[0][0] )
                
                # Only run once
                self._exec = False
            else:
                om.out.debug('Could not determine the page language using ' + response.getURL() +', not enough text to make a good analysis.')
                # Keep running until giving a good response...
                self._exec = True
        
        return []
    
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
        </OptionList>\
        '
    
    def end( self ):
        if self._exec:
            # I never got executed !
            om.out.information('Could not determine the language of the site. Enable discovery.webSpider and try again.')
    
    def setOptions( self, OptionList ):
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
        return ['discovery.error404page']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin reads N pages and determines the language the site is written in. This is done
        by saving a list of prepositions in different languages, and counting the number of matches
        on every page.
        '''
