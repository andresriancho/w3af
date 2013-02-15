'''
ajax.py

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

'''
import re
from lxml import etree

import core.data.kb.knowledge_base as kb

from core.controllers.plugins.grep_plugin import GrepPlugin
from core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from core.data.kb.info import Info


class ajax(GrepPlugin):
    '''
    Grep every page for traces of Ajax code.

    :author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        GrepPlugin.__init__(self)

        # Internal variables
        self._already_inspected = ScalableBloomFilter()

        # Create the regular expression to search for AJAX
        ajax_regex_string = '(XMLHttpRequest|eval\(|ActiveXObject|Msxml2\.XMLHTTP|'
        ajax_regex_string += 'ActiveXObject|Microsoft\.XMLHTTP)'
        self._ajax_regex_re = re.compile(ajax_regex_string, re.IGNORECASE)

        # Compile the XPATH
        self._script_xpath = etree.XPath('.//script')

    def grep(self, request, response):
        '''
        Plugin entry point.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, all results are saved in the kb.
        '''
        url = response.get_url()
        if response.is_text_or_html() and url not in self._already_inspected:

            # Don't repeat URLs
            self._already_inspected.add(url)

            dom = response.get_dom()
            # In some strange cases, we fail to normalize the document
            if dom is None:
                return
            
            script_elements = self._script_xpath(dom)
            for element in script_elements:
                # returns the text between <script> and </script>
                script_content = element.text

                if script_content is not None:

                    res = self._ajax_regex_re.search(script_content)
                    if res:
                        desc = 'The URL: "%s" has AJAX code.' % url
                        i = Info('AJAX code', desc, response.id,
                                 self.get_name())
                        i.set_url(url)
                        i.add_to_highlight(res.group(0))
                        
                        self.kb_append_uniq(self, 'ajax', i, 'URL')

    def get_long_desc(self):
        '''
        :return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every page for traces of Ajax code.
        '''
