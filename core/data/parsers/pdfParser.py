'''
pdfParser.py

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

try:
    import extlib.pyPdf.pyPdf as pyPdf
except:
    import pyPdf
    
import StringIO
import re

class pdfParser(abstractParser):
    '''
    This class parses pdf documents to find mails and URLs. It's based in the pyPdf library.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, httpResponse):
        abstractParser.__init__(self , httpResponse)
        self._parsed_URLs = []
        self._re_URLs = []
        
        # work !
        self._preParse( httpResponse.getBody() )
        
    def _preParse( self, document ):
        content_text = self.getPDFContent( document )
        self._parse( content_text )
    
    def _parse( self, content_text ):
        # Get the URLs using a regex
        url_regex = '((http|https):[A-Za-z0-9/](([A-Za-z0-9$_.+!*(),;/?:@&~=-])|%[A-Fa-f0-9]{2})+(#([a-zA-Z0-9][a-zA-Z0-9$_.+!*(),;/?:@&~=%-]*))?)'
        self._re_URLs = [ x[0] for x in re.findall(url_regex, content_text ) ]
        
        # Get the mail addys
        self.findEmails( content_text )
        
    def getPDFContent( self, documentString ):
        content = ""
        # Load PDF into pyPDF
        pdf = pyPdf.PdfFileReader( StringIO.StringIO(documentString) )
        try:
            
            # Iterate pages
            for i in range(0, pdf.getNumPages()):
                # Extract text from page and add to content
                content += pdf.getPage(i).extractText() + "\n"
            # Collapse whitespace
            content = " ".join(content.replace("\xa0", " ").strip().split())
            
        except Exception, e:
            om.out.debug('Exception in getPDFContent() , error: ' + str(e) )
            content = ''
        
        
        '''
        Added to avoid this bug:
        ===============
        
        "/home/ulises2k/programas/w3af-svn/w3af/core/data/parsers/abstractParser.py
        ", line 52, in findAccounts
        if line.count('@'+self._baseDomain):
        UnicodeDecodeError: 'ascii' codec can't decode byte 0xc3 in position 13:
        ordinal not in range(128)
        '''
        res = unicode(content,'utf-8','ignore').encode('utf-8')
        return res
    
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
