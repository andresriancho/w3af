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
import w3af.core.data.parsers.parser_cache as parser_cache

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.parsers.utils.form_constants import INPUT_TYPE_PASSWD
from w3af.core.data.kb.info import Info
from w3af.core.data.kb.info_set import InfoSet


class form_autocomplete(GrepPlugin):
    """
    Grep every page for detection of forms with 'autocomplete' capabilities
    containing password-type inputs.

    :author: Javier Andalia (jandalia =at= gmail.com)
    :author: Andres Riancho (andres.riancho =at= gmail.com)
    """
    def grep(self, request, response):
        """
        Plugin entry point, test existence of HTML auto-completable forms
        containing password-type inputs. Either form's <autocomplete> attribute
        is not present or is 'off'.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, all results are saved in the kb.
        """
        if not response.is_text_or_html():
            return

        try:
            doc_parser = parser_cache.dpc.get_document_parser_for(response)
        except BaseFrameworkException:
            return

        for form in doc_parser.get_forms():

            # Only analyze forms which have autocomplete enabled at <form>
            if form.get_autocomplete() is False:
                continue

            for form_field_list in form.meta.itervalues():
                for form_field in form_field_list:
                    if form_field.input_type != INPUT_TYPE_PASSWD:
                        continue

                    if not form_field.autocomplete:
                        continue

                    url = response.get_url()
                    desc = ('The URL: "%s" has a "<form>" element with '
                            'auto-complete enabled.')
                    desc %= url

                    i = Info('Auto-completable form', desc, response.id,
                             self.get_name())
                    i.add_to_highlight('autocomplete')
                    i.set_url(url)
                    i[AutoCompleteInfoSet.ITAG] = form.get_action().uri2url()

                    self.kb_append_uniq_group(self, 'form_autocomplete', i,
                                              group_klass=AutoCompleteInfoSet)
                    break

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page for autocomplete-able forms containing 
        password-type inputs.
        """


class AutoCompleteInfoSet(InfoSet):
    ITAG = 'action'
    TEMPLATE = (
        'The application contains {{ uris|length }} different URLs with a'
        ' <form> element which has auto-complete enabled for password fields.'
        ' The first {{ uris|sample_count }} vulnerable URLs are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )
