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
    
    
    def __init__(self, httpResponse, normalizeMarkup=True, verbose=0):
        self._tagsContainingURLs =  ('a', 'img', 'link', 'script', 'iframe', 'object',
                'embed', 'area', 'frame', 'applet', 'input', 'base',
                'div', 'layer', 'ilayer', 'bgsound', 'form')
        self._urlAttrs = ('href', 'src', 'data', 'action' )
        
        # An internal list to be used to save input tags that are found outside
        # of the scope of a form tag.
        self._saved_inputs = []
        self._saved_selects = []
        
        sgmlParser.__init__(self, httpResponse, normalizeMarkup, verbose)
        
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
            self._handle_form_tag(tag, attrs)
        
        # I changed the logic of this section of the parser because of this bug:
        # http://groups.google.com/group/beautifulsoup/browse_thread/thread/21ecff548dfda934/469d45ac13dc0162#469d45ac13dc0162
        # That the guys from BeautifulSoup ignored :S
        if tag.lower() in ['input','select', 'option', 'textarea']:
            
            # I may be inside a form tag or not... damn bug!
            # I'm going to use this ruleset:
            # - If there is an input tag outside a form, and there is no form in self._forms
            #   then I'm going to "save" the input tag until I find a form, and then I'll put
            #   it there.
            #
            # - If there is an input tag outside a form, and there IS a form in self._forms
            #   then I'm going to append the input tag to that form
            if self._insideForm:
                method = getattr(self, '_handle_'+tag.lower()+'_tag_inside_form')
                method(tag, attrs)
                
            else:
                # Outside a form!
                method = getattr(self, '_handle_'+tag.lower()+'_tag_outside_form')
                method(tag, attrs)
    
    def _handle_form_tag(self, tag, attrs):
        '''
        Handles the form tags.
        
        This method also looks if there are "pending inputs" in the self._saved_inputs list
        and parses them.
        '''
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
                action = urlParser.urlJoin( self._baseUrl, attr[1] )
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
            
        # Now I verify if they are any input tags that were found outside the scope of a form tag
        for tag, attrs in self._saved_inputs:
            # Parse them just like if they were found AFTER the form tag opening
            self._handle_input_tag_inside_form(tag, attrs)
        # All parsed, remove them.
        self._saved_inputs = []
    
    def _handle_input_tag_inside_form(self, tag, attrs):
        # We are working with the last form
        f = self._forms[-1]

        # Try to get the type of input
        for attr in attrs:
            if attr[0].lower() == 'type' and attr[1].lower() == 'file':
                # Let the form know, that this is a file input
                f.hasFileInput = True
                f.addFileInput( attrs )
                return
        
        # Simply add all the other input types
        f.addInput( attrs )

    def _handle_input_tag_outside_form(self, tag, attrs):
        # I'm going to use this ruleset:
        # - If there is an input tag outside a form, and there is no form in self._forms
        #   then I'm going to "save" the input tag until I find a form, and then I'll put
        #   it there.
        #
        # - If there is an input tag outside a form, and there IS a form in self._forms
        #   then I'm going to append the input tag to that form
        if not self._forms:
            self._saved_inputs.append( (tag, attrs) )
        else:
            self._handle_input_tag_inside_form(tag, attrs)

    def _handle_textarea_tag_inside_form(self, tag, attrs):
        """
        Handler for textarea tag inside a form
        """
        try:
            self._textareaTagName = [ v[1] for v in attrs if v[0].lower() in ['name','id'] ][0]
        except Exception,  e:
            om.out.debug('htmlParser found a textarea tag without a name attr, IGNORING!')
            self._insideTextarea = False
        else:
            self._insideTextarea = True

    def handle_data(self, data):
        """
        This method is called to process arbitrary data.
        """
        attrs = []
        if self._insideTextarea:
            f = self._forms[-1]
            attrs.append( ('name',self._textareaTagName) )
            attrs.append( ('value', data) )
            f.addInput( attrs )
            self._insideTextarea = False

    def _handle_textarea_tag_outside_form(self, tag, attrs):
        """
        Handler for textarea tag outside a form
        """
         ### TODO: Code this!
        pass

    def _handle_select_tag_inside_form(self, tag, attrs):
        try:
            self._selectTagName = [ v[1] for v in attrs if v[0].lower() in ['name','id'] ][0]
        except Exception,  e:
            om.out.debug('htmlParser found a select tag without a name attr, IGNORING!')
            self._insideSelect = False
        else:
            self._insideSelect = True

    def _handle_select_tag_outside_form(self, tag, attrs):
        ### TODO: Code this!
        pass
    
    def _handle_option_tag_inside_form(self, tag, attrs):    
        if self._insideSelect:
            # We are working with the last form
            f = self._forms[-1]
            attrs.append( ('name',self._selectTagName) ) 
            f.addInput( attrs )
    
    def _handle_option_tag_outside_form(self, tag, attrs):    
        ### TODO: Code this!
        pass

