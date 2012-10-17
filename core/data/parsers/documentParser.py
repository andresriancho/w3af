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
from core.controllers.w3afException import w3afException

import core.data.parsers.htmlParser as htmlParser
import core.data.parsers.pdfParser as pdfParser
import core.data.parsers.swfParser as swfParser
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
    
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    def __init__(self, HTTPResponse):

        # Create the proper parser instance, please note that
        # the order in which we ask for the type is not random,
        # first we discard the images which account for a great
        # % of the URLs in a site, then we ask for WML which is
        # a very specific thing to match, then we try text or HTML
        # which is very generic (if we would have exchanged these two
        # we would have never got to WML), etc.
        if HTTPResponse.is_image():
            msg = 'There is no parser for images.'
            raise w3afException(msg)
        elif self._isWML(HTTPResponse):
            parser = wmlParser.wmlParser(HTTPResponse)
        elif HTTPResponse.is_text_or_html():
            parser = htmlParser.HTMLParser(HTTPResponse)
        elif self._isPDF(HTTPResponse):
            parser = pdfParser.pdfParser(HTTPResponse)
        elif self._isSWF(HTTPResponse):
            parser = swfParser.swfParser(HTTPResponse)
        else:
            msg = 'There is no parser for "%s".' % HTTPResponse.getURL()
            raise w3afException(msg)
        
        self._parser = parser
    
    def _isPDF(self, HTTPResponse):
        '''
        @HTTPResponse: A http response object that contains a document of type HTML / PDF / WML / etc.
        @return: True if the document parameter is a string that contains a PDF document.
        '''
        if HTTPResponse.content_type in ('application/x-pdf', 'application/pdf'):
            document = HTTPResponse.body
            
            #   With the objective of avoiding this bug:
            #   https://sourceforge.net/tracker/?func=detail&atid=853652&aid=2954220&group_id=170274
            #   I perform this safety check:
            if not document:
                return False
        
            #   Some PDF files don't end with %%EOF, they end with
            #   things like %%EOF\n , or %%EOF\r, or %%EOF\r\n. 
            #   So... just to be sure I search in the last 12 characters.
            if document.startswith('%PDF-') and '%%EOF' in document[-12:]:
                try:
                    pyPdf.PdfFileReader( StringIO.StringIO(document) )
                except Exception:
                    return False
                else:
                    return True
        
        return False
    
    def _isSWF(self, HTTPResponse):
        '''
        @return: True if the HTTPResponse contains a SWF file.
        '''
        if HTTPResponse.content_type == 'application/x-shockwave-flash':
            
            body = HTTPResponse.getBody()
        
            if len(body) > 5:
                magic = body[:3]
            
                # TODO: Add more checks here?
                if magic in ('FWS', 'CWS'):
                    return True
        
        return False
    
    WML_RE = re.compile('<!DOCTYPE wml PUBLIC', re.IGNORECASE)
    
    def _isWML( self, HTTPResponse ):
        '''
        @HTTPResponse: A http response object that contains a document of type HTML / PDF / WML / etc.
        @return: True if the document parameter is a string that contains a WML document.
        '''
        if HTTPResponse.content_type == 'text/vnd.wap.wml':
        
            document = HTTPResponse.getBody()
        
            if self.WML_RE.search( document ):
                return True
        
        return False
        
    def getForms( self ):
        '''
        @return: A list of forms.
        '''
        return self._parser.getForms()
        
    def getReferences( self ):
        '''
        @return: A tuple that contains two lists:
            * URL objects extracted through parsing,
            * URL objects extracted through RE matching
        
        Returned in two separate lists because the first ones
        are much more accurate and they might deserve a different
        treatment.
        '''
        return self._parser.getReferences()
    
    def getReferencesOfTag( self, tag ):
        '''
        @parameter tag: A tag object.
        @return: A list of references related to the tag that is passed as parameter.
        '''
        return self._parser.getReferencesOfTag( tag )
        
    def getEmails( self, domain=None ):
        '''
        @parameter domain: Indicates what email addresses I want to retrieve:   "*@domain".
        @return: A list of email accounts that are inside the document.
        '''
        return self._parser.getEmails( domain )
    
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
    
    
def document_parser_factory(HTTPResponse):
    return documentParser(HTTPResponse)