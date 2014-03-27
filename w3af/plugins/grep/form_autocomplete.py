"""
form_autocomplete.py

Copyright 2010 Andres Riancho

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
from itertools import chain
from lxml import etree

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.info import Info

# Find all form elements that don't include the'autocomplete' attribute;
# otherwise (if included) not equals 'off'
AUTOCOMPLETE_FORMS_XPATH = ("//form[not(@autocomplete) or "
                            "translate(@autocomplete,'OF','of')!='off']")
# Find all input elements which type's lower-case value
# equals-case-sensitive 'password'
PWD_INPUT_XPATH = "//input[translate(@type,'PASWORD','pasword')='password']"
# All 'text' input elements
TEXT_INPUT_XPATH = "//input[translate(@type,'TEXT','text')='text']"


class form_autocomplete(GrepPlugin):
    """
    Grep every page for detection of forms with 'autocomplete' capabilities
    containing password-type inputs.

    :author: Javier Andalia (jandalia =at= gmail.com)
    """

    def __init__(self):
        GrepPlugin.__init__(self)

        # Internal variables
        self._autocomplete_forms_xpath = etree.XPath(AUTOCOMPLETE_FORMS_XPATH)
        self._pwd_input_xpath = etree.XPath(PWD_INPUT_XPATH)
        self._text_input_xpath = etree.XPath(TEXT_INPUT_XPATH)

    def grep(self, request, response):
        """
        Plugin entry point, test existance of HTML auto-completable forms
        containing password-type inputs. Either form's <autocomplete> attribute
        is not present or is 'off'.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, all results are saved in the kb.
        """
        url = response.get_url()
        dom = response.get_dom()

        if not response.is_text_or_html() or dom is None:
            return

        autocompletable = lambda inp: inp.get('autocomplete', 'on').lower() != 'off'

        # Loop through "auto-completable" forms
        for form in self._autocomplete_forms_xpath(dom):

            passwd_inputs = self._pwd_input_xpath(form)

            # Test existence of password-type inputs and verify that
            # all inputs are autocompletable
            if passwd_inputs and all(map(autocompletable,
                                         chain(passwd_inputs,
                                               self._text_input_xpath(form)))):

                desc = 'The URL: "%s" has a "<form>" element with ' \
                       'auto-complete enabled.'
                desc = desc % url

                i = Info('Auto-completable form', desc, response.id,
                         self.get_name())
                i.set_url(url)

                form_str = etree.tostring(form)
                to_highlight = form_str[:(form_str).find('>') + 1]
                i.add_to_highlight(to_highlight)

                # Store and print
                kb.kb.append(self, 'form_autocomplete', i)
                om.out.information(desc)

                break

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """\
        This plugin greps every page for autocomplete-able forms containing 
        password-type inputs.
        """
