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

from lxml import etree

from core.data.parsers.sgmlParser import sgmlParser
from core.data.parsers.urlParser import url_object

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
        self._textareaData = ""
        self._optionAttrs = []
        # Save for using in form parsing
        self._source_url = httpResponse.getURL()
        
        sgmlParser.__init__(self, httpResponse, normalizeMarkup, verbose)
        
    def _preParse( self, httpResponse ):
        '''
        @parameter httpResponse: The HTTP response document that contains the
        HTML document inside its body.
        '''
        assert self._baseUrl, 'The base URL must be set.'
        
        HTMLDocument = httpResponse.getBody()
    
        if self._normalizeMarkup:
            HTMLDocument = httpResponse.getNormalizedBody() or ''

        # Now we are ready to work
        self._parse (HTMLDocument)
        
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
                action = self._baseUrl.urlJoin( attr[1] )
                action = self._decode_URL( action , self._encoding)
                foundAction = True

        if not foundAction:
            msg = 'htmlParser found a form without an action attribute. Javascript may be used...'
            msg += ' but another option (mozilla does this) is that the form is expected to be '
            msg += ' posted back to the same URL (the one that returned the HTML that we are '
            msg += ' parsing).'
            om.out.debug(msg)
            action = self._source_url

        # Create the form object and store everything for later use
        self._insideForm = True
        form_obj = form.form()
        form_obj.setMethod( method )
        form_obj.setAction( action )
        self._forms.append( form_obj )

        # Now I verify if they are any input tags that were found outside the scope of a form tag
        for tag, attrs in self._saved_inputs:
            # Parse them just like if they were found AFTER the form tag opening
            self._handle_input_tag_inside_form(tag, attrs)
        # All parsed, remove them.
        self._saved_inputs = []

    def _handle_input_tag_inside_form(self, tag, attrs):
        # We are working with the last form
        form_obj = self._forms[-1]

        # Try to get the type of input
        for attr in attrs:
            
            #
            #   FIXME: This is a kludge. Should we get lists as attr?!
            #
            if isinstance(attr, list):
                try:
                    attr = attr[0]
                except:
                    return
            
            if attr[0].lower() == 'type' and attr[1].lower() == 'file':
                # Let the form know, that this is a file input
                form_obj.hasFileInput = True
                form_obj.addFileInput( attrs )
                return
            if attr[0].lower() == 'type' and attr[1].lower() == 'radio':
                form_obj.addRadio( attrs )
                return
            if attr[0].lower() == 'type' and attr[1].lower() == 'checkbox':
                form_obj.addCheckBox( attrs )
                return

        # Simply add all the other input types
        form_obj.addInput( attrs )

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
        self._textareaData = ''
        
        # Get the name
        self._textareaTagName = ''
        for attr in attrs:
            if attr[0].lower() == 'name':
                self._textareaTagName = attr[1]
        
        if not self._textareaTagName:
            for attr in attrs:
                if attr[0].lower() == 'id':
                    self._textareaTagName = attr[1]
            
        if not self._textareaTagName:    
            om.out.debug('htmlParser found a textarea tag without a name attr, IGNORING!')
            self._insideTextarea = False
        else:
            self._insideTextarea = True
            if self._forms:
                form_obj = self._forms[-1]
                form_obj.addInput([('name', self._textareaTagName), ('value', '')])

    def handle_data(self, data):
        """
        This method is called to process arbitrary data.
        """
        if self._insideTextarea:
            self._textareaData = data

    def _handle_textarea_tag_outside_form(self, tag, attrs):
        """
        Handler for textarea tag outside a form
        """
        self._handle_textarea_tag_inside_form(tag, attrs)

    def _handle_textarea_endtag(self):
        """
        Handler for textarea end tag
        """
        sgmlParser._handle_textarea_endtag(self)
        if not self._forms:
            self._saved_inputs.append( ('input', attrs) )
        else:
            form_obj = self._forms[-1]
            # Replace with real value
            form_obj[self._textareaTagName][-1] = self._textareaData

    def _handle_select_tag_inside_form(self, tag, attrs):
        """
        Handler for select tag inside a form
        """
        self._optionAttrs = []
        
        # Get the name
        self._selectTagName = ''
        for attr in attrs:
            if attr[0].lower() == 'name':
                self._selectTagName = attr[1]
        
        if not self._selectTagName:
            for attr in attrs:
                if attr[0].lower() == 'id':
                    self._selectTagName = attr[1]
            
        if not self._selectTagName:            
            om.out.debug('htmlParser found a select tag without a name attr, IGNORING!')
            self._insideSelect = False
        else:
            self._insideSelect = True

    def _handle_select_tag_outside_form(self, tag, attrs):
        """
        Handler for select tag outside a form
        """
        self._handle_select_tag_inside_form(tag, attrs)

    def _handle_select_endtag(self):
        """
        Handler for select end tag
        """
        sgmlParser._handle_select_endtag(self)
        if not self._forms:
            self._saved_inputs.append( ('input', self._optionAttrs) )
        else:
            form_obj = self._forms[-1]
            form_obj.addSelect( self._selectTagName, self._optionAttrs )

    def _handle_option_tag_inside_form(self, tag, attrs):
        """
        Handler for option tag inside a form
        """
        if self._insideSelect:
            self._optionAttrs.append(attrs)

    def _handle_option_tag_outside_form(self, tag, attrs):
        """
        Handler for option tag outside a form
        """
        self._handle_option_tag_inside_form(tag, attrs)
