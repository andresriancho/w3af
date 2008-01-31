'''
wmlParser.py

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

from core.data.parsers.sgmlParser import sgmlParser
import core.data.parsers.urlParser as urlParser

import core.data.dc.form as form


class wmlParser(sgmlParser):
    '''
    This class is a WML parser. WML is used in cellphone "web" pages.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, document, baseUrl, verbose=0):
        self._tagsContainingURLs =  ('go', 'a','anchor','img', 'link', 'script', 'iframe', 'object',
                'embed', 'area', 'frame', 'applet', 'input', 'base',
                'div', 'layer', 'ilayer', 'bgsound', 'form')
        self._urlAttrs = ('href', 'src', 'data', 'action' )
        
        sgmlParser.__init__(self, document, baseUrl, verbose)
        
    def _preParse( self, WMLDocument ):
        assert self._baseUrl != '', 'The base URL must be setted.'
        # Now we are ready to work
        self._parse ( WMLDocument )
        
    def unknown_endtag(self, tag):         
        '''
        called for each end tag, e.g. for </pre>, tag will be "pre"
        '''
        if tag == 'go' :
            self._insideForm = False
        
        if tag == 'select' :
            self._insideSelect = False
        
    def _findForms(self, tag, attrs):
        '''
        This method finds forms inside an WML document.
        '''
        
        '''
        <go method="post" href="dataReceptor.php">
            <postfield name="clave" value="$(clave)"/>
            <postfield name="cuenta" value="$(cuenta)"/>
            <postfield name="tipdat" value="D"/>
        </go>
        '''
        if tag == 'go' :
            #Find the method
            method = 'GET'
            foundMethod = False
            for attr in attrs:
                if attr[0] == 'method':
                    method = attr[1]
                    foundMethod = True
            
            if not foundMethod:
                om.out.debug('wmlParser found a form without a method. Using GET as the default.')
            
            #Find the action
            foundAction = False
            for attr in attrs:
                if attr[0] == 'href':
                    action = urlParser.urlJoin( self._baseUrl ,attr[1] )
                    foundAction = True
                    
            if not foundAction:
                om.out.debug('wmlParser found a form without an action. Javascript is being used.')
                # <form name="frmRegistrar" onsubmit="valida();">
            else:
                self._insideForm = True
                f = form.form()
                f.setMethod( method )           
                f.setAction( action )
                self._forms.append( f )
        
        if self._insideForm:
            # I am inside a form, I should parse input tags
            if tag in [ 'input', 'postfield','setvar' ]:
                # We are working with the last form
                f = self._forms[ len(self._forms) -1 ]
                f.addInput( attrs )
                    
            elif tag == 'select':
                self._insideSelect = True
                try:
                    self._selectTagName = [ v[1] for v in attrs if v[0] in ['name','id'] ][0]
                except:
                    om.out.debug('wmlParser found a select tag without a name attr !')
            
            if self._insideSelect:
                if tag == 'option':
                    # We are working with the last form in the list
                    f = self._forms[ len(self._forms) -1 ]
                    attrs.append( ('name',self._selectTagName) ) 
                    f.addInput( attrs )

    
