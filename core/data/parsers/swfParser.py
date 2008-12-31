'''
swfParser.py

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
from core.data.parsers.abstractParser import abstractParser
    
import zlib


class swfParser(abstractParser):
    '''
    This class is a SWF (flash) parser. This is the first version, so don't expect much!
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, httpResponse):
        abstractParser.__init__(self , httpResponse)
        
        # To store results
        self._parsed_URLs = []
        self._re_URLs = []
        
        # work !
        swf = httpResponse.getBody()
        if self._is_compressed( swf ):
            try:
                swf = self._inflate( swf )
            except Exception, e:
                # If the inflate fails... there is nothing else to do.
                return
        
        http_response_copy = httpResponse.copy()
        http_response_copy.setBody(swf)
        
        self._parse( http_response_copy )
    
    def _is_compressed(self, swf_document):
        '''
        
        @parameter swf_content: The SWF file.
        @return: True if the SWF is compressed
        '''
        return swf_document.startswith('CWS')
        
    def _inflate( self, swf_document ):
        '''
        zlib.inflate the SWF file.
        
        @parameter swf_content: The SWF file.
        @return: A decompressed version of the SWF
        '''
        compressed_data = swf_document[8:]
        try:
            uncompressed_data = zlib.decompress(compressed_data)
        except zlib.error, e:
            raise Exception('Failed to inflate: ' + str(e))
        else:
            return uncompressed_data
    
    def _parse( self, swf_response ):
        '''
        Parse the SWF bytecode.
        
        For now... don't decompile anything, just apply regular expressions to it.
        
        @parameter swf_response: An httpResponse containing the SWF
        '''
        self._regex_url_parse( swf_response )
    
    def getReferences( self ):
        '''
        Searches for references on a page. w3af searches references in every html tag, including:
            - a
            - forms
            - images
            - frames
            - etc.
        
        @return: Two lists, one with the parsed URLs, and one with the URLs that came out of a
        regular expression. The second list if less trustworthy.
        '''        
        tmp_re_URLs = set(self._re_URLs) - set( self._parsed_URLs )
        return list(set( self._parsed_URLs )), list(tmp_re_URLs)
        
    def _returnEmptyList( self ):
        '''
        This method is called (see below) when the caller invokes one of:
            - getForms
            - getComments
            - getMetaRedir
            - getMetaTags
            - getReferencesOfTag
        
        @return: Because we are a PDF document, we don't have the same things that
        a nice HTML document has, so we simply return an empty list.
        '''
        return []
        
    getReferencesOfTag = getForms = getComments = getMetaRedir = getMetaTags = _returnEmptyList
