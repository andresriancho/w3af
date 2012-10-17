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

import zlib

from core.data.parsers.baseparser import BaseParser
    

class swfParser(BaseParser):
    '''
    This class is a SWF (flash) parser. This is the first version, so don't expect much!
    
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    def __init__(self, HTTPResponse):
        BaseParser.__init__(self , HTTPResponse)
        
        # work !
        swf = HTTPResponse.getBody()
        if self._is_compressed(swf):
            try:
                swf = self._inflate(swf)
            except Exception:
                # If the inflate fails... there is nothing else to do.
                return
        
        self._parse(swf)
    
    def _is_compressed(self, swf_document):
        '''
        
        @parameter swf_content: The SWF file.
        @return: True if the SWF is compressed
        '''
        return swf_document.startswith('CWS')
        
    def _inflate(self, swf_document):
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
            # TODO: Strings in SWF are NULL-Byte delimited. Maybe we can
            # use that to extract strings and apply regular expressions
            # more carefully?
            return uncompressed_data
    
    def _parse(self, swf_body):
        '''
        Parse the SWF bytecode.
        For now... don't decompile anything, just apply regular
        expressions to it.
        
        @param swf_body: SWF bytecode string
        '''
        # FIXME: Jan 2012, JAP - Now this method does nothing. Extracting
        # urls from a compiled flash leads to serious encoding issues
        # while performing scans. The definite solution is to decompile
        # swf files and decode the proper substrings (urls in swf files
        # are found in specific sections) using the proper encoding name.
        ##self._regex_url_parse(swf_body)
        pass
    
    def getReferences(self):
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
        return ([], list(self._re_urls))
        
    def _returnEmptyList(self, *args, **kwds):
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

