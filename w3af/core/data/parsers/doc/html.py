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

from w3af.core.data.parsers.doc.sgml import SGMLParser
from w3af.core.data.parsers.utils.re_extract import ReExtract
from w3af.core.data.parsers.utils.form_params import (FormParameters,
                                                      DEFAULT_FORM_ENCODING)


class HTMLParser(SGMLParser):
    """
    This class parses HTML's.

    @authors: Andres Riancho (andres.riancho@gmail.com)
              Javier Andalia (jandalia =AT= GMAIL.COM)
    """

    # http://www.freeformatter.com/mime-types-list.html
    IGNORE_CONTENT_TYPES = ('application', 'video', 'audio', 'image',
                            'chemical', 'model')
    WILD_ACCEPT_CONTENT_TYPES = ('text', 'message')
    SPECIFIC_ACCEPT_CONTENT_TYPES = ('text/html', 'application/hta',
                                     'application/xhtml+xml', 'application/xml')

    PARSE_TAGS = SGMLParser.PARSE_TAGS.union({'form', 'input', 'textarea',
                                              'select', 'option'})

    def __init__(self, http_resp):
        # An internal list to be used to save input tags found
        # outside of the scope of a form tag.
        self._saved_inputs = []

        # For <textarea> elems parsing
        self._textarea_tag_name = ''
        self._textarea_data = ''

        # For <select> elems parsing
        self._selects = []

        # Save for using in form parsing
        self._source_url = http_resp.get_url()

        self._re_urls = set()

        # Call parent's __init__
        SGMLParser.__init__(self, http_resp)

    @staticmethod
    def can_parse(http_resp):
        """
        :param http_resp: A http response object that contains a document of
                          type HTML / PDF / WML / etc.

        :return: True if the document parameter is a string that contains an
                 HTML document. Since we're trying to extract as many links as
                 possible, and the internet is an ugly place (where content
                 type headers are not mandatory) we'll be very forgiving and
                 return True when we're unsure about the content-type.
        """
        content_type = http_resp.content_type.lower()

        if content_type == '':
            # We get here when the remote server doesn't send a content-type
            # and the HTTPResponse parser will set it to an empty string
            #
            # Lets parse it...
            return True

        if content_type in HTMLParser.SPECIFIC_ACCEPT_CONTENT_TYPES:
            return True

        try:
            ct_type, ct_subtype = content_type.split('/')
        except ValueError:
            # The content type doesn't have the expected format type/subtype
            # won't parse something that's completely broken
            return False

        if ct_subtype.startswith('vnd.'):
            return False

        if ct_type in HTMLParser.WILD_ACCEPT_CONTENT_TYPES:
            return True

        if ct_type in HTMLParser.IGNORE_CONTENT_TYPES:
            return False

        return False

    def _handle_script_tag_start(self, tag, tag_name, attrs):
        """
        Handle the script tags
        """
        SGMLParser._handle_script_tag_start(self, tag, tag_name, attrs)
        
        if tag.text is not None:
            re_extract = ReExtract(tag.text.strip(),
                                   self._base_url,
                                   self._encoding)
            self._re_urls.update(re_extract.get_references())

    @property
    def references(self):
        """
        Override to return the references parsed from the JavaScript code using
        regular expressions.
        """
        parsed_urls = [url for tag, url in self._tag_and_url]
        return parsed_urls, list(self._re_urls - set(parsed_urls))

    def _form_elems_generic_handler(self, tag, tag_name, attrs):
        side = 'inside' if self._inside_form else 'outside'
        default = lambda *args: None
        handler = '_handle_%s_tag_%s_form' % (tag_name, side)
        meth = getattr(self, handler, default)
        meth(tag, tag_name, attrs)

    def _handle_form_tag_start(self, tag, tag_name, attrs):
        """
        Handle the form tags.

        This method also looks if there are "pending inputs" in the
        self._saved_inputs list and parses them.
        """
        SGMLParser._handle_form_tag_start(self, tag, tag_name, attrs)

        method = attrs.get('method', 'GET').upper()
        action = attrs.get('action', None)
        form_encoding = attrs.get('enctype', DEFAULT_FORM_ENCODING)
        autocomplete = attrs.get('autocomplete', None)

        if action is None:
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
        form_params = FormParameters(encoding=self._encoding)
        form_params.set_method(method)
        form_params.set_action(action)
        form_params.set_form_encoding(form_encoding)
        form_params.set_autocomplete(autocomplete)

        self._forms.append(form_params)

        # Now I verify if there are any input tags that were found
        # outside the scope of a form tag
        for input_attrs in self._saved_inputs:
            # Parse them just like if they were found AFTER the
            # form tag opening
            self._handle_input_tag_inside_form(tag, 'input', input_attrs)

        # All parsed, remove them.
        self._saved_inputs = []

    def close(self):
        """
        Called by the parser when it ends
        """
        SGMLParser.close(self)

        # Cleanup
        self._saved_inputs = []

    ## <input> handler methods
    _handle_input_tag_start = _form_elems_generic_handler

    def _handle_input_tag_inside_form(self, tag, tag_name, attrs):
        # We are working with the last form
        form_params = self._forms[-1]
        items = attrs.items()

        # Simply add all the other input types
        form_params.add_input(items)

    def _handle_input_tag_outside_form(self, tag, tag_name, attrs):
        # I'm going to use this rule set:
        #
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
            self._handle_input_tag_inside_form(tag, tag_name, attrs)

    ## <textarea> handler methods
    _handle_textarea_tag_start = _form_elems_generic_handler

    def _handle_textarea_tag_inside_form(self, tag, tag_name, attrs):
        """
        Handler for textarea tag inside a form
        """
        # Set the data and name
        self._textarea_data = tag.text
        self._textarea_tag_name = attrs.get('name', '') or attrs.get('id', '')

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
            form_params = self._forms[-1]
            form_params.add_input(attrs.items())

    ## <select> handler methods
    _handle_select_tag_start = _form_elems_generic_handler

    def _handle_select_tag_end(self, tag):
        """
        Handler for select end tag
        """
        SGMLParser._handle_select_tag_end(self, tag)
        if self._forms:
            form_params = self._forms[-1]
            for sel_name, optvalues in self._selects:
                # First convert  to list of tuples before passing it as arg
                optvalues = [tuple(attrs.items()) for attrs in optvalues]
                form_params.add_select(sel_name, optvalues)

            # Reset selects container
            self._selects = []

    def _handle_select_tag_inside_form(self, tag, tag_name, attrs):
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

    def _handle_option_tag_inside_form(self, tag, tag_name, attrs):
        """
        Handler for option tag inside a form
        """
        if self._inside_select:
            self._selects[-1][1].append(attrs)

    _handle_option_tag_outside_form = _handle_option_tag_inside_form
