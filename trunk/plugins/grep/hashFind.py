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
from core.data.bloomfilter.pybloom import ScalableBloomFilter

import re


class hashFind(baseGrepPlugin):
    '''
    Identify hashes in HTTP responses.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        self._already_reported = ScalableBloomFilter()
        
        # regex to split between words
        self._split_re = re.compile('[^\w]')
        
        
    def grep(self, request, response):
        '''
        Plugin entry point, identify hashes in the HTTP response.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        # I know that by doing this I loose the chance of finding hashes in PDF files, but...
        # This is much faster
        if response.is_text_or_html():
            
            body = response.getBody()
            splitted_body = self._split_re.split(body)
            for possible_hash in splitted_body:
                
                #    This is a performance enhancement that cuts the execution
                #    time of this plugin in half.
                if len(possible_hash) > 31:
                
                    hash_type = self._get_hash_type( possible_hash )
                    if hash_type:
                        if self._has_hash_distribution( possible_hash ):
                            if (possible_hash, response.getURL()) not in self._already_reported:
                                i = info.info()
                                i.setPluginName(self.getName())
                                i.setName( hash_type + 'hash in HTML content')
                                i.setURL( response.getURL() )
                                i.addToHighlight(possible_hash)
                                i.setId( response.id )
                                msg = 'The URL: "'+ response.getURL()  + '" returned a response that may'
                                msg += ' contain a "' + hash_type + '" hash. The hash is: "'+ possible_hash
                                msg += '". This is uncommon and requires human verification.'
                                i.setDesc( msg )
                                kb.kb.append( self, 'hashFind', i )
                                
                                self._already_reported.add( (possible_hash, response.getURL()) )
    
    def _has_hash_distribution( self, possible_hash ):
        '''
        @parameter possible_hash: A string that may be a hash.
        @return: True if the string s has an equal(aprox.) distribution of numbers and letters
        '''
        numbers = 0
        letters = 0
        for char in possible_hash:
            if char.isdigit():
                numbers += 1
            else:
                letters += 1
        
        if numbers in range( letters - len(possible_hash) / 2 , letters + len(possible_hash) / 2 ):
            # Seems to be a hash, let's make a final test to avoid false positives with
            # strings like:
            # 2222222222222222222aaaaaaaaaaaaa
            is_hash = True
            for char in possible_hash:
                if possible_hash.count(char) > len(possible_hash) / 5:
                    is_hash = False
                    break
            return is_hash
            
        else:
            return False
        
    def _get_hash_type( self, possible_hash ):
        '''
        @parameter possible_hash: A string that may be a hash.
        @return: The hash type if the string seems to be a md5 / sha1 hash.
        None otherwise.
        '''
        # FIXME: Add more here!
        if len( possible_hash ) == 32:
            return 'MD5'
        elif len( possible_hash ) == 40:
            return 'SHA1'
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
        self.printUniq( kb.kb.getData( 'hashFind', 'hashFind' ), None )
    
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
