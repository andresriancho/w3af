"""
svn_users.py

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
import re

import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.vuln import Vuln


class svn_users(GrepPlugin):
    """
    Grep every response for users of the versioning system.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        GrepPlugin.__init__(self)

        # Add the regex to match something like this:
        #
        #   $Id: lzio.c,v 1.24 2003/03/20 16:00:56 roberto Exp $
        #   $Id: file name, version, timestamp, creator Exp $
        #
        regex = '\$.{1,12}: .*? .*? \d{4}[-/]\d{1,2}[-/]\d{1,2}'
        regex += ' \d{1,2}:\d{1,2}:\d{1,2}.*? (.*?) (Exp )?\$'
        self._regex_list = [re.compile(regex), ]

    def grep(self, request, response):
        """
        Plugin entry point.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, all results are saved in the kb.
        """
        if not response.is_text_or_html():
            return

        uri = response.get_uri()

        for regex in self._regex_list:
            for m in regex.findall(response.get_body()):
                user = m[0]
                
                desc = 'The URL: "%s" contains a SVN versioning signature'\
                       ' with the username "%s".'
                desc = desc % (uri, user)
                
                v = Vuln('SVN user disclosure vulnerability', desc,
                         severity.LOW, response.id, self.get_name())

                v.set_uri(uri)
                v['user'] = user
                v.add_to_highlight(user)
                
                self.kb_append_uniq(self, 'users', v, 'URL')

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page for users of the versioning system. Sometimes
        the HTML pages are versioned using CVS or SVN, if the header of the
        versioning system is saved as a comment in this page, the user that edited
        the page will be saved on that header and will be added to the knowledge
        base.
        """
