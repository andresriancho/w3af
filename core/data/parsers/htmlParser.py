'''
htmlParser.py

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
import core.data.kb.config as cf
try:
    import extlib.BeautifulSoup as BeautifulSoup
    om.out.debug('htmlParser is using the bundled BeautifulSoup library')
except:
    try:
        import BeautifulSoup
        om.out.debug('htmlParser is using the systems BeautifulSoup library')
    except:
        raise w3afException('You have to install BeautifulSoup lib.')

from core.data.parsers.sgmlParser import sgmlParser
import core.data.parsers.urlParser as urlParser

import core.data.dc.form as form

class htmlParser(sgmlParser):
    '''
    This class parses HTML's.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    
    def __init__(self, document, baseUrl, normalizeMarkup=True, verbose=0):
        self._tagsContainingURLs =  ('a','img', 'link', 'script', 'iframe', 'object',
                'embed', 'area', 'frame', 'applet', 'input', 'base',
                'div', 'layer', 'ilayer', 'bgsound', 'form')
        self._urlAttrs = ('href', 'src', 'data', 'action' )
        
        sgmlParser.__init__(self, document, baseUrl, normalizeMarkup, verbose)
        
    def _preParse( self, HTMLDocument ):
        assert self._baseUrl != '', 'The base URL must be setted.'
        if self._normalizeMarkup:
            try:
                HTMLDocument = str( BeautifulSoup.BeautifulSoup(HTMLDocument) )
            except Exception,e:
                om.out.debug('BeautifulSoup raised the exception:' + str(e))
                om.out.debug('Parsing HTML document without BeautifulSoup normalization.')

        # Now we are ready to work
        self._parse ( HTMLDocument )
        
    def _findForms(self, tag, attrs):
        '''
        This method finds forms inside an HTML document.
        '''
        
        '''
        <FORM action="http://somesite.com/prog/adduser" method="post">
        <P>
                <LABEL for="firstname">First name: </LABEL>
                <INPUT type="text" id="firstname"><BR>
                <LABEL for="lastname">Last name: </LABEL>
                <INPUT type="text" id="lastname"><BR>
                <LABEL for="email">email: </LABEL>
                <INPUT type="text" id="email"><BR>
                <INPUT type="radio" name="sex" value="Male"> Male<BR>
                <INPUT type="radio" name="sex" value="Female"> Female<BR>
                <INPUT type="submit" value="Send"> <INPUT type="reset">
        </P>
        </FORM>
        '''
        
        if tag.lower() == 'form' :
            #Find the method
            method = 'GET'
            foundMethod = False
            for attr in attrs:
                if attr[0].lower() == 'method':
                    method = attr[1].upper()
                    foundMethod = True
            
            if not foundMethod:
                om.out.debug('htmlParser found a form without a method. Using GET as the default.')
            
            #Find the action
            foundAction = False
            for attr in attrs:
                if attr[0].lower() == 'action':
                    action = urlParser.urlJoin( self._baseUrl ,attr[1] )
                    foundAction = True
                    
            if not foundAction:
                om.out.debug('htmlParser found a form without an action. Javascript is being used.')
                # <form name="frmRegistrar" onsubmit="valida();">
            else:
                self._insideForm = True
                f = form.form()
                f.setMethod( method )           
                f.setAction( action )
                self._forms.append( f )
        
        if self._insideForm:
            # We are working with the last form
            f = self._forms[ len(self._forms) -1 ]

            # I am inside a form, I should parse input tags
            if tag.lower() == 'input':
                # Get the type
                for attr in attrs:
                    if attr[0].lower() == 'type':
                        break
                # Let the form know, that this is a file input
                if attr[1].lower() == 'file':
                    f.hasFileInput = True
                    f.addFileInput( attrs )
                    
                # Simply add all the other input types
                f.addInput( attrs )
                    
                    
            elif tag.lower() == 'select':
                self._insideSelect = True
                try:
                    self._selectTagName = [ v[1] for v in attrs if v[0].lower() in ['name','id'] ][0]
                except:
                    om.out.debug('htmlParser found a select tag without a name attr !')
            
            if self._insideSelect:
                if tag.lower() == 'option':
                    attrs.append( ('name',self._selectTagName) ) 
                    f.addInput( attrs )


