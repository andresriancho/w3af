'''
hashFind.py

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
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
import re
from core.data.getResponseType import *

class hashFind(baseGrepPlugin):
    '''
    Identify hashes in HTTP responses.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
    def _testResponse(self, request, response):
        
        # I know that by doing this I loose the chance of finding hashes in PDF files, but...
        # This is much faster
        if isTextOrHtml( response.getHeaders() ):
            
            body = response.getBody()
            splittedBody = re.split( '[^\w]', body )
            for s in splittedBody:
                hashType = self._hasHashLen( s )
                if hashType:
                    if self._hasHashDistribution( s ):
                        i = info.info()
                        i.setName('Hash in HTML content')
                        i.setURL( response.getURL() )
                        i.setId( response.id )
                        i.setDesc( 'The URL: "'+ response.getURL()  + '" returned a response that may contain a '+hashType+' hash. The string is: "'+ s +'". This is uncommon and requires human verification.')
                        kb.kb.append( self, 'hashFind', i )
    
    def _hasHashDistribution( self, s ):
        '''
        @return: True if the string s has an equal(aprox.) distribution of numbers and letters
        '''
        numbers = 0
        letters = 0
        for c in s:
            if c.isdigit():
                numbers += 1
            else:
                letters += 1
        
        if numbers in range( letters - len(s) / 2 , letters + len(s) / 2 ):
            # Seems to be a hash, let's make a final test to avoid false positives with strings like:
            # 2222222222222222222aaaaaaaaaaaaa
            isHash = True
            for c in s:
                if s.count(c) > len(s) / 5:
                    isHash = False
                    break
            return isHash
            
        else:
            return False
        
    def _hasHashLen( self, s ):
        '''
        @return: True if the string has a lenght of a md5 / sha1 hash.
        '''
        if len( s ) == 32:
            return 'md5'
        elif len( s ) == 40:
            return 'sha1'
        else:
            return None
    
    def setOptions( self, OptionList ):
        pass
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.printUniq( kb.kb.getData( 'hashFind', 'hashFind' ), 'URL' )
    
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
        This plugin identifies hashes in HTTP responses.
        '''
