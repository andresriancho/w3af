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
import core.data.parsers.urlParser as urlParser
import string
import re
from sgmllib import SGMLParser
from core.data.parsers.abstractParser import abstractParser as abstractParser

class sgmlParser(abstractParser, SGMLParser):
    '''
    This class is a SGML document parser.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    

    def __init__(self, document, baseUrl, normalizeMarkup=True, verbose=0):
        abstractParser.__init__( self, baseUrl )
        SGMLParser.__init__(self, verbose)

        self._tagsContainingURLs =  ('go', 'a','img', 'link', 'script', 'iframe', 'object',
                'embed', 'area', 'frame', 'applet', 'input', 'base',
                'div', 'layer', 'ilayer', 'bgsound', 'form')
        self._urlAttrs = ('href', 'src', 'data', 'action' )
        
        self._urlsInDocumentWithTags = []
        
        #########
        # Regex URL detection ( normal detection is also done, see below )
        #########
        #urlRegex = '((http|https):[A-Za-z0-9/](([A-Za-z0-9$_.+!*(),;/?:@&~=-])|%[A-Fa-f0-9]{2})+(#([a-zA-Z0-9][a-zA-Z0-9$_.+!*(),;/?:@&~=%-]*))?)'
        urlRegex = '((http|https)://([\w\.]*)/[^ \n\r\t"]*)'
        self._urlsInDocument = [ x[0] for x in re.findall(urlRegex, document ) ]
        
        # Now detect some relative URL's ( also using regexs )
        def findRelative( doc ):
            res = []
            relRegex = re.compile('[^\/\/]([\/][A-Z0-9a-z%_~\.]+)+\.[A-Za-z0-9]{1,4}(((\?)([a-zA-Z0-9]*=\w*)){1}((&)([a-zA-Z0-9]*=\w*))*)?')
            
            go = True
            while go:
                try:
                    s, e = relRegex.search( doc ).span()
                except:
                    go = False
                else:
                    res.append( urlParser.urlJoin( baseUrl , doc[s+1:e] ) )
                    doc = doc[e:]
            '''
            om.out.debug('Relative URLs found using regex:')
            for u in res:
                om.out.debug('- ' + u )
            '''
            return res
        
        relativeURLs = findRelative( document )
        self._urlsInDocument.extend( relativeURLs )
        ########
        # End
        ########
        
        self._forms = []
        self._insideForm = False
        self._insideSelect = False
        self._commentsInDocument = []
        
        # mail accounts
        self._accounts = []
        
        # Meta tags
        self._metaRedirs = []
        self._metaTags = []
        
        self._normalizeMarkup = normalizeMarkup
        
        # Now we are ready to work
        self._preParse( document )

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
        try:
            self._findReferences(tag, attrs)
            self._findForms(tag, attrs)
        
            if tag.lower() == 'meta':
                self._parseMetaTags(tag, attrs)
        except Exception, e:
            om.out.error('An unhandled exception was found while parsing a document. The exception is: "' + str(e) + '"')
    
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
                time, url = content.split(';')
                url = url.strip()
                url = url[4:]
                url = urlParser.urlJoin( self._baseUrl , url )
                self._urlsInDocument.append( url )
                self._urlsInDocumentWithTags.append( ('meta', url ) )
    
    def _findReferences(self, tag, attrs):
        '''
        This method finds references inside a document.
        '''
        if tag.lower() in self._tagsContainingURLs:
            for attr in attrs:
                if attr[0].lower() in self._urlAttrs:
                    if len(  attr[1] ):
                            if attr[1][0] != '#':
                                url = urlParser.urlJoin( self._baseUrl ,attr[1] )
                                if url not in self._urlsInDocument:
                                    self._urlsInDocument.append( url )
                                    self._urlsInDocumentWithTags.append( (tag.lower(), url) )
                                    break
    
    def _parse(self, s):
        '''
        This method parses the document.
        
        @parameter s: The document to parse.
        '''
        try:
            self.findAccounts( s )
            self.feed(s)
            self.close()
        except Exception, e:
            # The user will call getAccounts, getReferences, etc and will get all the information
            # that the parser could find before dieing
            om.out.debug('Exception found while parsing document. Exception: ' + str(e) )
        else:
            # Saves A LOT of memory
            # without this a run will use 4,799,936
            # with this, a run will use 113,696
            del self.rawdata
        
        
    def getAccounts( self ):
        return self._accounts
    
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
        
        @return: Returns list of links.
        '''
        return set( self._urlsInDocument )
        
    def getReferencesOfTag( self, tagType ):
        '''
        @return: A list of the URLs that the parser found in a tag of tagType = "tagType" (i.e img, a)
        '''
        return [ x[1] for x in self._urlsInDocumentWithTags if x[0] == tagType ]
        
    def getComments( self ):
        '''
        @return: Returns list of comment strings.
        '''
        return set( self._commentsInDocument )
    
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
        self._commentsInDocument.append( text )
        
