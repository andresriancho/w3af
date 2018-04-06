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
from w3af.core.data.parsers.doc.sgml import SGMLParser
from w3af.core.data.parsers.utils.form_params import FormParameters
from w3af.core.data.parsers.utils.form_fields import get_value_by_key


WML_HEADER = '<!DOCTYPE wml PUBLIC'.lower()


class WMLParser(SGMLParser):
    """
    This class is a WML parser. WML is used in cellphone "web" pages.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    PARSE_TAGS = SGMLParser.TAGS_WITH_URLS.union({'go', 'postfield',
                                                  'setvar', 'input',
                                                  'select', 'option'})

    def __init__(self, http_response):
        self._select_tag_name = ''
        self._source_url = http_response.get_url()

        SGMLParser.__init__(self, http_response)

    @staticmethod
    def can_parse(http_resp):
        """
        :param http_resp: A http response object that contains a document of
                          type HTML / PDF / WML / etc.

        :return: True if the document parameter is a string that contains a
                 WML document.
        """
        if 'wml' not in http_resp.content_type:
            return False

        document = http_resp.get_body().lower()

        if WML_HEADER in document:
            return True

        return False

    def _handle_go_tag_start(self, tag, tag_name, attrs):
        self._inside_form = True
        method = attrs.get('method', 'GET').upper()
        action = attrs.get('href', None)

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

        # Create the form
        f = FormParameters(encoding=self._encoding,
                           attributes=attrs,
                           hosted_at_url=self._source_url)
        f.set_method(method)
        f.set_action(action)

        self._forms.append(f)

    def _handle_go_tag_end(self, tag):
        self._inside_form = False

    def _handle_input_tag_start(self, tag, tag_name, attrs):
        if not self._inside_form:
            return

        # We are working with the last form
        f = self._forms[-1]
        f.add_field_by_attrs(attrs)

    def _handle_select_tag_start(self, tag, tag_name, attrs):
        if not self._inside_form:
            return

        self._select_tag_name = get_value_by_key(attrs, 'name', 'id')

        if self._select_tag_name:
            self._inside_select = True
        else:
            self._inside_select = False

    def _handle_option_tag_start(self, tag, tag_name, attrs):
        if not self._inside_form:
            return

        if not self._inside_select:
            return

        # Working with the last form in the list
        f = self._forms[-1]
        attrs['name'] = self._select_tag_name
        f.add_field_by_attrs(attrs)

    _handle_postfield_tag_start = _handle_input_tag_start
    _handle_setvar_tag_start = _handle_input_tag_start
