'''
abstractParser.py

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

import core.data.dc.form as form
import core.data.parsers.urlParser as urlParser
import string
import re

class abstractParser:
    '''
    This class is an abstract document parser.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__( self, baseUrl ):
        # "setBaseUrl"
        self._baseUrl = baseUrl
        self._baseDomain = urlParser.getDomain(baseUrl)
    
    def findAccounts( self , documentString ):
        '''
        @return: A list with all mail users that are present in the documentString.
        '''
        if documentString.find('@') != -1:
            # This two for loops were taken from Sergio Alvarez fingergoogle.py
            for i in ('=','"', '\'','<br>', '[', ']', '<', '>', ':', ';', '&', '(', ')', '{', '}'):
                documentString = string.replace(documentString, i, ' ')
            documentString = string.split(documentString, '\n')
            for line in documentString:
                if line.count('@'+self._baseDomain):
                    split = string.split(line, ' ')
                    for i in split:
                        if i.count('@'+self._baseDomain):
                            if i[0] == '@':
                                continue
                            if string.split(i, '@')[1] != self._baseDomain:
                                continue
                            i = i[:-(len(self._baseDomain)+1)]
                            if len(i) > 1:
                                if i[-1] == '@':
                                    i = i[:-1]
                            # If account aint in account list , then add
                            if self._accounts.count(i) == 0:
                                self._accounts.append(i)

    def getAccounts( self ):
        raise Exception('You should create your own parser class and implement the getAccounts() method.')
    
    def getForms( self ):
        raise Exception('You should create your own parser class and implement the getForms() method.')
        
    def getReferences( self ):
        raise Exception('You should create your own parser class and implement the getReferences() method.')
        
    def getComments( self ):
        raise Exception('You should create your own parser class and implement the getComments() method.')
        
    def getMetaRedir( self ):
        '''
        @return: Returns list of meta redirections.
        '''
        raise Exception('You should create your own parser class and implement the getMetaRedir() method.')
    
    def getMetaTags( self ):
        '''
        @return: Returns list of all meta tags.
        '''
        raise Exception('You should create your own parser class and implement the getMetaTags() method.')
        
