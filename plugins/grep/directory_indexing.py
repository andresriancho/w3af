'''
directory_indexing.py

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
import core.data.kb.knowledge_base as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

from core.controllers.plugins.grep_plugin import GrepPlugin
from core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from core.data.esmre.multi_in import multi_in


class directory_indexing(GrepPlugin):
    '''
    Grep every response for directory indexing problems.

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    DIR_INDEXING = (
        "<title>Index of /",
        '<a href="?C=N;O=D">Name</a>',
        '<A HREF="?M=A">Last modified</A>',
        "Last modified</a>",
        "Parent Directory</a>",
        "Directory Listing for",
        "<TITLE>Folder Listing.",
        '<table summary="Directory Listing" ',
        "- Browsing directory ",
        # IIS 6.0 and 7.0
        '">[To Parent Directory]</a><br><br>',
        # IIS 5.0
        '<A HREF=".*?">.*?</A><br></pre><hr></body></html>'
    )
    _multi_in = multi_in(DIR_INDEXING)

    def __init__(self):
        GrepPlugin.__init__(self)

        self._already_visited = ScalableBloomFilter()

    def grep(self, request, response):
        '''
        Plugin entry point, search for directory indexing.
        @param request: The HTTP request object.
        @param response: The HTTP response object
        @return: None
        '''
        if response.get_url().get_domain_path() in self._already_visited:
            # Already worked for this URL, no reason to work twice
            return

        else:
            # Save it,
            self._already_visited.add(response.get_url().get_domain_path())

            # Work,
            if response.is_text_or_html():
                html_string = response.get_body()
                for dir_indexing_match in self._multi_in.query(html_string):
                    v = vuln.vuln()
                    v.set_plugin_name(self.get_name())
                    v.set_url(response.get_url())
                    msg = 'The URL: "' + \
                        response.get_url() + '" has a directory '
                    msg += 'indexing vulnerability.'
                    v.set_desc(msg)
                    v.set_id(response.id)
                    v.set_severity(severity.LOW)
                    path = response.get_url().get_path()
                    v.set_name('Directory indexing - ' + path)
                    kb.kb.append(self, 'directory', v)
                    break

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.print_uniq(kb.kb.get('directory_indexing', 'directory'), 'URL')

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every response directory indexing problems.
        '''
