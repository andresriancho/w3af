'''
documentParser.py

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

import core.data.parsers.htmlParser as htmlParser
import core.data.parsers.pdfParser as pdfParser
import core.data.parsers.wmlParser as wmlParser

try:
    from extlib.pyPdf import pyPdf as pyPdf
except ImportError:
    import pyPdf
    
import StringIO
import re

class documentParser:
    '''
    This class is a document parser.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, document, baseUrl, normalizeMarkup=True):
        if self._isWML( document ):
            self._parser = wmlParser.wmlParser( document, baseUrl )
        elif self._isPDF( document ):
            self._parser = pdfParser.pdfParser( document, baseUrl )
        else:
            self._parser = htmlParser.htmlParser( document, baseUrl, normalizeMarkup)
    
    def _isPDF( self, document ):
        '''
        @document: A string that contains a document of type HTML / PDF / WML / etc.
        @return: True if the document parameter is a string that contains a PDF document.
        '''
        if document.startswith('%PDF-'):
            try:
                pyPdf.PdfFileReader( StringIO.StringIO(document) )
            except Exception:
                return False
            else:
                return True
        else:
            return False
            
    def _isWML( self, document ):
        '''
        @document: A string that contains a document of type HTML / PDF / WML / etc.
        @return: True if the document parameter is a string that contains a WML document.
        '''
        if re.search('<!DOCTYPE wml PUBLIC',  document,  re.IGNORECASE) and\
        re.search('<html', document, re.IGNORECASE):
            return True
        else:
            return False
            
    def getForms( self ):
        '''
        @return: A list of forms.
        '''
        return self._parser.getForms()
        
    def getReferences( self ):
        '''
        @return: A list of URL strings.
        '''
        return list( self._parser.getReferences() )
    
    def getReferencesOfTag( self, tag ):
        '''
        @parameter tag: A tag object.
        @return: A list of references related to the tag that is passed as parameter.
        '''
        return self._parser.getReferencesOfTag( tag )
        
    def getAccounts( self ):
        '''
        @return: A list of email accounts that are inside the document.
        '''
        return self._parser.getAccounts()
    
    def getComments( self ):
        '''
        @return: A list of comments.
        '''
        return self._parser.getComments()
    
    def getScripts( self ):
        '''
        @return: A list of scripts (like javascript).
        '''
        return self._parser.getScripts()
        
    def getMetaRedir( self ):
        '''
        @return: A list of the meta redirection tags.
        '''
        return self._parser.getMetaRedir()
        
    def getMetaTags( self ):
        '''
        @return: A list of all meta tags.
        '''
        return self._parser.getMetaTags()
    
    
