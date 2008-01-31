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

import core.controllers.outputManager as om

import core.data.parsers.htmlParser as htmlParser
import core.data.parsers.pdfParser as pdfParser
import core.data.parsers.wmlParser as wmlParser

from core.controllers.w3afException import w3afException
import extlib.pyPdf.pyPdf as pyPdf
import StringIO

class documentParser:
    '''
    This class is a document parser.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, document, baseUrl, normalizeMarkup=True, verbose=0):
        if self._isWML( document ):
            self._parser = wmlParser.wmlParser( document, baseUrl)
        elif self._isPDF( document ):
            self._parser = pdfParser.pdfParser( document, baseUrl )
        else:
            self._parser = htmlParser.htmlParser( document, baseUrl, normalizeMarkup)
    
    def _isPDF( self, document ):
        if document.startswith('%PDF-'):
            try:
                pyPdf.PdfFileReader( StringIO.StringIO(document) )
            except Exception, e:
                return False
            else:
                return True
        else:
            return False
            
    def _isWML( self, document ):
        if document.count('<!DOCTYPE wml PUBLIC'):
            return True
        else:
            return False
            
    def getForms( self ):
        return self._parser.getForms()
        
    def getReferences( self ):
        return list( self._parser.getReferences() )
    
    def getReferencesOfTag( self, tag ):
        return self._parser.getReferencesOfTag( tag )
        
    def getAccounts( self ):
        return self._parser.getAccounts()
    
    def getComments( self ):
        return self._parser.getComments()
        
    def getMetaRedir( self ):
        return self._parser.getMetaRedir()
        
    def getMetaTags( self ):
        return self._parser.getMetaTags()
    
    
