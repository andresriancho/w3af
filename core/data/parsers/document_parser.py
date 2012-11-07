'''
DocumentParser.py

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
import StringIO
import re

try:
    from extlib.pyPdf import pyPdf as pyPdf
except ImportError:
    import pyPdf

import core.data.parsers.htmlParser as htmlParser
import core.data.parsers.pdf as PDFParser
import core.data.parsers.swfParser as swfParser
import core.data.parsers.wmlParser as wmlParser

from core.controllers.w3afException import w3afException


class DocumentParser(object):
    '''
    This class is a document parser.
    
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    def __init__(self, http_resp):

        # Create the proper parser instance, please note that
        # the order in which we ask for the type is not random,
        # first we discard the images which account for a great
        # % of the URLs in a site, then we ask for WML which is
        # a very specific thing to match, then we try text or HTML
        # which is very generic (if we would have exchanged these two
        # we would have never got to WML), etc.
        if http_resp.is_image():
            msg = 'There is no parser for images.'
            raise w3afException(msg)
        elif self._is_wml(http_resp):
            parser = wmlParser.wmlParser(http_resp)
        elif http_resp.is_text_or_html():
            parser = htmlParser.HTMLParser(http_resp)
        elif self._is_pdf(http_resp):
            parser = PDFParser.PDFParser(http_resp)
        elif self._is_swf(http_resp):
            parser = swfParser.swfParser(http_resp)
        else:
            msg = 'There is no parser for "%s".' % http_resp.getURL()
            raise w3afException(msg)
        
        self._parser = parser
    
    def _is_pdf(self, http_resp):
        '''
        @param http_resp: A http response object that contains a document of
                          type HTML / PDF / WML / etc.
        
        @return: True if the document parameter is a string that contains a PDF
                 document.
        '''
        if http_resp.content_type in ('application/x-pdf', 'application/pdf'):
            document = http_resp.body
            
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
    
    def _is_swf(self, http_resp):
        '''
        @return: True if the http_resp contains a SWF file.
        '''
        if http_resp.content_type == 'application/x-shockwave-flash':
            
            body = http_resp.getBody()
        
            if len(body) > 5:
                magic = body[:3]
            
                # TODO: Add more checks here?
                if magic in ('FWS', 'CWS'):
                    return True
        
        return False
    
    WML_RE = re.compile('<!DOCTYPE wml PUBLIC', re.IGNORECASE)
    
    def _is_wml( self, http_resp ):
        '''
        @param http_resp: A http response object that contains a document of
                          type HTML / PDF / WML / etc.
                          
        @return: True if the document parameter is a string that contains a
                 WML document.
        '''
        if http_resp.content_type == 'text/vnd.wap.wml':
        
            document = http_resp.getBody()
        
            if self.WML_RE.search( document ):
                return True
        
        return False
        
    def get_forms( self ):
        '''
        @return: A list of forms.
        '''
        return self._parser.get_forms()
        
    def get_references( self ):
        '''
        @return: A tuple that contains two lists:
            * URL objects extracted through parsing,
            * URL objects extracted through RE matching
        
        Returned in two separate lists because the first ones
        are much more accurate and they might deserve a different
        treatment.
        '''
        return self._parser.get_references()
    
    def get_references_of_tag( self, tag ):
        '''
        @param tag: A tag object.
        @return: A list of references related to the tag that is passed as parameter.
        '''
        return self._parser.get_references_of_tag( tag )
        
    def get_emails( self, domain=None ):
        '''
        @param domain: Indicates what email addresses I want to retrieve:   "*@domain".
        @return: A list of email accounts that are inside the document.
        '''
        return self._parser.get_emails( domain )
    
    def get_comments( self ):
        '''
        @return: A list of comments.
        '''
        return self._parser.get_comments()
    
    def get_scripts( self ):
        '''
        @return: A list of scripts (like javascript).
        '''
        return self._parser.get_scripts()
        
    def get_meta_redir( self ):
        '''
        @return: A list of the meta redirection tags.
        '''
        return self._parser.get_meta_redir()
        
    def get_meta_tags( self ):
        '''
        @return: A list of all meta tags.
        '''
        return self._parser.get_meta_tags()
    
    
def document_parser_factory(http_resp):
    return DocumentParser(http_resp)