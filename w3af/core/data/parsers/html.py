"""
html.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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

"""
import w3af.core.controllers.output_manager as om
import w3af.core.data.dc.form as form

from w3af.core.data.parsers.sgml import SGMLParser


class HTMLParser(SGMLParser):
    """
    This class parses HTML's.

    @authors: Andres Riancho (andres.riancho@gmail.com)
              Javier Andalia (jandalia =AT= GMAIL.COM)
    """

    def __init__(self, http_resp):

        # An internal list to be used to save input tags found
        # outside of the scope of a form tag.
        self._saved_inputs = []
        # For <textarea> elems parsing
        self._textarea_tag_name = ""
        self._textarea_data = ""
        # For <select> elems parsing
        self._selects = []
        # Save for using in form parsing
        self._source_url = http_resp.get_url()
        # Call parent's __init__
        SGMLParser.__init__(self, http_resp)

    def data(self, data):
        """
        Overriding parent's. Called by the main parser when a text node
        is found
        """
        if self._inside_textarea:
            self._textarea_data = data.strip()

    def _pre_parse(self, http_resp):
        """
        :param http_resp: The HTTP response document that contains the
        HTML document inside its body.
        """
        SGMLParser._pre_parse(self, http_resp)
        assert self._base_url, 'The base URL must be set.'

    def _form_elems_generic_handler(self, tag, attrs):
        side = 'inside' if self._inside_form else 'outside'
        default = lambda *args: None
        meth = getattr(self,
                       '_handle_' + tag + '_tag_' + side + '_form',
                       default)
        meth(tag, attrs)

    ## <form> handler methods
    def _handle_form_tag_start(self, tag, attrs):
        """
        Handle the form tags.

        This method also looks if there are "pending inputs" in the
        self._saved_inputs list and parses them.
        """
        SGMLParser._handle_form_tag_start(self, tag, attrs)

        # Get the 'method'
        method = attrs.get('method', 'GET').upper()

        # Get the action
        action = attrs.get('action', None)
        missing_action = action is None

        if missing_action:
            action = self._source_url
        else:
            action = self._decode_url(action)
            try:
                action = self._base_url.url_join(action, encoding=self._encoding)
            except ValueError:
                # The URL in the action is invalid, the best thing we can do
                # is to guess, and our best guess is that the URL will be the
                # current one.
                action = self._source_url

        # Create the form object and store everything for later use
        form_obj = form.Form(encoding=self._encoding)
        form_obj.set_method(method)
        form_obj.set_action(action)
        self._forms.append(form_obj)

        # Now I verify if there are any input tags that were found
        # outside the scope of a form tag
        for inputattrs in self._saved_inputs:
            # Parse them just like if they were found AFTER the
            # form tag opening
            if isinstance(inputattrs, dict):
                self._handle_input_tag_inside_form('input', inputattrs)

        # All parsed, remove them.
        self._saved_inputs = []

    ## <input> handler methods
    _handle_input_tag_start = _form_elems_generic_handler

    def _handle_input_tag_inside_form(self, tag, attrs):

        # We are working with the last form
        form_obj = self._forms[-1]
        _type = attrs.get('type', '').lower()
        items = attrs.items()

        if _type == 'file':
            # Let the form know, that this is a file input
            form_obj.hasFileInput = True
            form_obj.add_file_input(items)
        elif _type == 'radio':
            form_obj.add_radio(items)
        elif _type == 'checkbox':
            form_obj.add_check_box(items)
        else:
            # Simply add all the other input types
            form_obj.add_input(items)

    def _handle_input_tag_outside_form(self, tag, attrs):
        # I'm going to use this ruleset:
        # - If there is an input tag outside a form, and there is
        #   no form in self._forms then I'm going to "save" the input
        #   tag until I find a form, and then I'll put it there.
        #
        # - If there is an input tag outside a form, and there IS a
        #   form in self._forms then I'm going to append the input
        #   tag to that form
        if not self._forms:
            self._saved_inputs.append(attrs)
        else:
            self._handle_input_tag_inside_form(tag, attrs)

    ## <textarea> handler methods
    _handle_textarea_tag_start = _form_elems_generic_handler

    def _handle_textarea_tag_inside_form(self, tag, attrs):
        """
        Handler for textarea tag inside a form
        """
        # Reset data
        self._textarea_data = ""
        # Get the name
        self._textarea_tag_name = attrs.get('name', '') or \
            attrs.get('id', '')

        if not self._textarea_tag_name:
            om.out.debug('HTMLParser found a textarea tag without a '
                         'name attr, IGNORING!')
            self._inside_textarea = False
        else:
            self._inside_textarea = True

    _handle_textarea_tag_outside_form = _handle_textarea_tag_inside_form

    def _handle_textarea_tag_end(self, tag):
        """
        Handler for textarea end tag
        """
        SGMLParser._handle_textarea_tag_end(self, tag)
        attrs = {'name': self._textarea_tag_name,
                 'value': self._textarea_data}
        if not self._forms:
            self._saved_inputs.append(attrs)
        else:
            form_obj = self._forms[-1]
            form_obj.add_input(attrs.items())

    ## <select> handler methods
    _handle_select_tag_start = _form_elems_generic_handler

    def _handle_select_tag_end(self, tag):
        """
        Handler for select end tag
        """
        SGMLParser._handle_select_tag_end(self, tag)
        if self._forms:
            form_obj = self._forms[-1]
            for sel_name, optvalues in self._selects:
                # First convert  to list of tuples before passing it as arg
                optvalues = [tuple(attrs.items()) for attrs in optvalues]
                form_obj.add_select(sel_name, optvalues)

            # Reset selects container
            self._selects = []

    def _handle_select_tag_inside_form(self, tag, attrs):
        """
        Handler for select tag inside a form
        """
        # Get the name
        select_name = attrs.get('name', '') or attrs.get('id', '')

        if not select_name:
            om.out.debug('HTMLParser found a select tag without a '
                         'name attr, IGNORING!')
            self._inside_select = False
        else:
            self._selects.append((select_name, []))
            self._inside_select = True

    _handle_select_tag_outside_form = _handle_select_tag_inside_form

    ## <option> handler methods
    _handle_option_tag_start = _form_elems_generic_handler

    def _handle_option_tag_inside_form(self, tag, attrs):
        """
        Handler for option tag inside a form
        """
        if self._inside_select:
            self._selects[-1][1].append(attrs)

    _handle_option_tag_outside_form = _handle_option_tag_inside_form
