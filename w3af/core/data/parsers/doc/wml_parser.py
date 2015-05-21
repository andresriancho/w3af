"""
wml_parser.py

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
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.utils.form_params import FormParameters


WML_HEADER = '<!DOCTYPE wml PUBLIC'.lower()


class WMLParser(SGMLParser):
    """
    This class is a WML parser. WML is used in cellphone "web" pages.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    PARSE_TAGS = SGMLParser.TAGS_WITH_URLS.union({'go', 'postfield'})

    def __init__(self, http_response):
        self._select_tag_name = ""
        SGMLParser.__init__(self, http_response)

    @staticmethod
    def can_parse(http_resp):
        """
        :param http_resp: A http response object that contains a document of
                          type HTML / PDF / WML / etc.

        :return: True if the document parameter is a string that contains a
                 WML document.
        """
        if 'wml' in http_resp.content_type:

            document = http_resp.get_body().lower()

            if WML_HEADER in document:
                return True

        return False

    def _handle_go_tag_start(self, tag, tag_name, attrs):

        # Find method
        method = attrs.get('method', 'GET').upper()

        # Find action
        action = attrs.get('href', '')
        if action:
            self._inside_form = True
            action = unicode(self._base_url.url_join(action))
            action = URL(self._decode_url(action),
                         encoding=self._encoding)
            # Create the form
            f = FormParameters(encoding=self._encoding)
            f.set_method(method)
            f.set_action(action)
            self._forms.append(f)
        else:
            om.out.debug('WMLParser found a form without an action. '
                         'Javascript is being used.')

    def _handle_go_tag_end(self, tag):
        self._inside_form = False

    def _handle_input_tag_start(self, tag, tag_name, attrs):
        if self._inside_form:
            # We are working with the last form
            f = self._forms[-1]
            f.add_input(attrs.items())

    _handle_postfield_tag_start = \
        _handle_setvar_tag_start = _handle_input_tag_start

    def _handle_select_tag_start(self, tag, tag_name, attrs):
        if self._inside_form:
            self._select_tag_name = select_name = attrs.get('name', '') or \
                attrs.get('id', '')
            if select_name:
                self._inside_select = True
            else:
                om.out.debug('WMLParser found a select tag without a '
                             'name attr !')
                self._inside_select = False

    def _handle_option_tag_start(self, tag, tag_name, attrs):
        if self._inside_form and self._inside_select:
            # Working with the last form in the list
            f = self._forms[-1]
            attrs['name'] = self._select_tag_name
            f.add_input(attrs.items())
