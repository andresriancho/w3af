'''
sgmlParser.py

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
from core.data.parsers.abstractParser import abstractParser as abstractParser
from core.data.parsers.urlParser import url_object

from sgmllib import SGMLParser
import traceback
import re


class sgmlParser(abstractParser, SGMLParser):
    '''
    This class is a SGML document parser.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self, httpResponse, normalizeMarkup=True, verbose=0):
        abstractParser.__init__( self, httpResponse )
        SGMLParser.__init__(self, verbose)

        # Set some constants
        self._tagsContainingURLs =  ('go', 'a','img', 'link', 'script', 'iframe', 'object',
                'embed', 'area', 'frame', 'applet', 'input', 'base',
                'div', 'layer', 'ilayer', 'bgsound', 'form')
        self._urlAttrs = ('href', 'src', 'data', 'action' )
        
        # And some internal variables
        self._tag_and_url = []
        self._parsed_URLs = []
        self._re_URLs = []
        self._encoding = httpResponse.getCharset()
        self._forms = []
        self._insideForm = False
        self._insideSelect = False
        self._insideTextarea = False
        self._insideScript = False
        self._commentsInDocument = []
        self._scriptsInDocument = []
        
        # Meta tags
        self._metaRedirs = []
        self._metaTags = []
        
        self._normalizeMarkup = normalizeMarkup
        
        #    Fill self._re_URLs list with url objects
        self._regex_url_parse( httpResponse )
        
        # Now we are ready to work
        self._preParse( httpResponse )
        
    def _preParse(self, document):
        '''
        Parse the document!
        
        @parameter document: The document that we want to parse.
        '''
        raise w3afException('You have to override the _preParse method when subclassing sgmlParser class.')

    def _findForms(self, tag, attrs):
        '''
        Find forms.
        '''
        raise w3afException('You have to override the _findForms method when subclassing sgmlParser class.')

    def unknown_endtag(self, tag):         
        '''
        called for each end tag, e.g. for </pre>, tag will be "pre"
        '''
        if tag.lower() == 'form' :
            self._insideForm = False

        if tag.lower() == 'select' :
            self._handle_select_endtag()

        if tag.lower() == 'script':
            self._insideScript = False

        if tag.lower() == 'textarea' :
            self._handle_textarea_endtag()

    def _handle_textarea_endtag(self):
        """
        Handler for textarea end tag
        """
        self._insideTextarea = False

    def _handle_select_endtag(self):
        """
        Handler for select end tag
        """
        self._insideSelect = False

    def unknown_starttag(self, tag, attrs):
        '''
        Called for each start tag
        attrs is a list of (attr, value) tuples
        e.g. for <pre class="screen">, tag="pre", attrs=[("class", "screen")]

        Note that improperly embedded non-HTML code (like client-side Javascript)
        may be parsed incorrectly by the ancestor, causing runtime script errors.
        All non-HTML code must be enclosed in HTML comment tags (<!-- code -->)
        to ensure that it will pass through this parser unaltered (in handle_comment).
        '''
        # TODO: For some reason this method failed to work:
        #def _handle_base_starttag(self, tag, attrs):        
        # so I added this here... it's not good code... but... it works!
        if tag.lower() == 'base':
            # Get the href value and then join
            new_base_url = ''
            for attr in attrs:
                if attr[0].lower() == 'href':
                    new_base_url = attr[1]
                    break
            # set the new base URL
            self._baseUrl = self._baseUrl.urlJoin( new_base_url )
        
        if tag.lower() == 'script':
            self._insideScript = True
            
        try:
            self._findReferences(tag, attrs)
        except Exception, e:
            msg = 'An unhandled exception was found while finding references inside a document.'
            msg += ' The exception is: "' + str(e) + '"'
            om.out.error( msg )
            om.out.error('Error traceback: ' + str( traceback.format_exc() ) )

        try:
            self._findForms(tag, attrs)
        except Exception, e:
            msg = 'An unhandled exception was found while finding forms inside a document.'
            msg += 'The exception is: "' + str(e) + '"'
            om.out.error( msg )
            om.out.error('Error traceback: ' + str( traceback.format_exc() ) )

        try:        
            if tag.lower() == 'meta':
                self._parseMetaTags(tag, attrs)
        except Exception, e:
            msg = 'An unhandled exception was found while parsing meta tags inside a document.'
            msg += 'The exception is: "' + str(e) + '"'
            om.out.error( msg )
            om.out.error('Error traceback: ' + str( traceback.format_exc() ) )
    
    def _parseMetaTags( self, tag , attrs ):
        '''
        This method parses the meta tags and creates a list of tuples with their values.
        The only exception made here is for the meta redirections, that are handled with "_findMetaRedir".
        '''
        self._findMetaRedir( tag, attrs )
        self._metaTags.append( attrs )
        
    def _findMetaRedir( self, tag, attrs):
        '''
        Find meta tag redirections, like this one:
        <META HTTP-EQUIV="refresh" content="4;URL=http://www.f00.us/">
        '''
        if tag.lower() == 'meta':
            hasHTTP_EQUIV = False
            hasContent = False
            content = ''
            for attr in attrs:
                if attr[0].lower() == 'http-equiv' and attr[1].lower() == 'refresh':
                    hasHTTP_EQUIV = True
                if attr[0].lower() == 'content':
                    hasContent = True
                    content = attr[1]
                    
            if hasContent and hasHTTP_EQUIV:
                self._metaRedirs.append( content )
                
                # And finally I add the URL to the list of url's found in the document...
                # The content variables looks something like... "4;URL=http://www.f00.us/"
                # The content variables looks something like... "2; URL=http://www.f00.us/"
                # The content variables looks something like... "6  ; URL=http://www.f00.us/"
                for url_string in re.findall('.*?URL.*?=(.*)', content, re.IGNORECASE):
                    url_string = url_string.strip()
                    url_instance = self._baseUrl.urlJoin( url_string )
                    url_instance = self._decode_URL( url_instance, self._encoding ) 
                    
                    self._parsed_URLs.append( url_instance )
                    self._tag_and_url.append( ('meta', url_instance ) )
    
    def _findReferences(self, tag, attrs):
        '''
        This method finds references inside a document.
        '''
        if tag.lower() not in self._tagsContainingURLs:
            return

        for attr_name, attr_val in attrs:
            if attr_name.lower() in self._urlAttrs:
                
                # Only add it to the result of the current URL is not a fragment
                if attr_val and not attr_val.startswith('#'):
                    
                    url_instance = self._baseUrl.urlJoin( attr_val )
                    url_instance = self._decode_URL( url_instance, self._encoding)
                    url_instance.normalizeURL()
                    
                    if url_instance not in self._parsed_URLs:
                        self._parsed_URLs.append(url_instance)
                        self._tag_and_url.append((tag.lower(), url_instance))
                        break
    
    def _parse(self, s):
        '''
        This method parses the document.
        
        @parameter s: The document to parse (as a string)
        '''
        try:
            self.findEmails( s )
            self.feed(s)
            self.close()
        except Exception, e:
            # The user will call getEmails, getReferences, etc and will get all the information
            # that the parser could find before dieing
            om.out.debug('Exception found while parsing document. Exception: ' + str(e) + '. Document head: "' + s[0:20] +'".' )
            om.out.debug( 'Traceback for this error: ' + str( traceback.format_exc() ) )
        else:
            # Saves A LOT of memory
            # without this a run will use 4,799,936
            # with this, a run will use 113,696
            del self.rawdata
        
    def getForms( self ):
        '''
        @return: Returns list of forms.
        '''
        return self._forms
        
    def getReferences( self ):
        '''
        Searches for references on a page. w3af searches references in every html tag, including:
            - a
            - forms
            - images
            - frames
            - etc.
        
        @return: Two sets, one with the parsed URLs, and one with the URLs that came out of a
        regular expression. The second list is less trustworthy.
        '''
        tmp_re_URLs = set(self._re_URLs) - set( self._parsed_URLs )
        return list(set( self._parsed_URLs )), list(tmp_re_URLs)
        
    def getReferencesOfTag( self, tagType ):
        '''
        @return: A list of the URLs that the parser found in a tag of tagType = "tagType" (i.e img, a)
        '''
        return [ x[1] for x in self._tag_and_url if x[0] == tagType ]
        
    def getComments( self ):
        '''
        @return: Returns list of comment strings.
        '''
        return set( self._commentsInDocument )
    
    def getScripts( self ):
        '''
        @return: Returns list of scripts (mainly javascript, but can be anything)
        '''
        return set( self._scriptsInDocument )
        
    def getMetaRedir( self ):
        '''
        @return: Returns list of meta redirections.
        '''
        return self._metaRedirs
    
    def getMetaTags( self ):
        '''
        @return: Returns list of all meta tags.
        '''
        return self._metaTags
        
    def handle_comment( self , text ):
        '''
        This method is called by parse when a comment is found.
        '''
        if self._insideScript:
            self._scriptsInDocument.append( text )
        else:
            self._commentsInDocument.append( text )
        
