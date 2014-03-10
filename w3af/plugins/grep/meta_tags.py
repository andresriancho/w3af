"""
meta_tags.py

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
import w3af.core.data.parsers.parser_cache as parser_cache

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.kb.info import Info


class meta_tags(GrepPlugin):
    """
    Grep every page for interesting meta tags.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    """
    Can someone explain what this meta tag does?
    <meta name="verify-v1" content="/JBoXnwT1d7TbbWCwL8tXe+Ts2I2LXYrdnnK50g7kdY=" />

    Answer:
    That's one of the verification elements used by Google Sitemaps. When you sign up
    for Sitemaps you have to add that element to a root page to demonstrate to Google that
    you're the site owner. So there is probably a Sitemaps account for the site, if you
    haven't found it already.
    """
    INTERESTING_WORDS = {'user': None, 'pass': None, 'microsoft': None,
                         'visual': None, 'linux': None, 'source': None,
                         'author': None, 'release': None, 'version': None,
                         'verify-v1': 'Google Sitemap'}

    def __init__(self):
        GrepPlugin.__init__(self)

    
    def grep(self, request, response):
        """
        Plugin entry point, search for meta tags.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        if not response.is_text_or_html() or is_404(response):
            return

        try:
            dp = parser_cache.dpc.get_document_parser_for(response)
        except BaseFrameworkException:
            return

        meta_tag_list = dp.get_meta_tags()

        for tag in meta_tag_list:
            tag_name = self._find_name(tag)
            for key, val in tag.items():

                for word in self.INTERESTING_WORDS:

                    # Check if we have something interesting
                    # and WHERE that thing actually is
                    where = content = None
                    if (word in key):
                        where = 'name'
                        content = key
                    elif (word in val):
                        where = 'value'
                        content = val

                    # Now... if we found something, report it =)
                    if where is not None:
                        # The atribute is interesting!
                        fmt = 'The URI: "%s" sent a <meta> tag with attribute'\
                              ' %s set to "%s" which looks interesting.'
                        desc = fmt % (response.get_uri(), where, content)
                        
                        if self.INTERESTING_WORDS.get(tag_name, None):
                            usage = self.INTERESTING_WORDS[tag_name]
                            desc += ' The tag is used for %s.' % usage
                        
                        i = Info('Interesting META tag', desc, response.id,
                                 self.get_name())
                        i.set_uri(response.get_uri())
                        i.add_to_highlight(where, content)

                        self.kb_append_uniq(self, 'meta_tags', i, 'URL')

    def _find_name(self, tag):
        """
        :return: the tag name.
        """
        for key, value in tag.items():
            if key.lower() == 'name':
                return value
        return ''

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page for interesting meta tags. Some interesting
        meta tags are the ones that contain : 'microsoft', 'visual', 'linux' .
        """
