"""
feeds.py

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
from lxml import etree

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.info import Info


class feeds(GrepPlugin):
    """
    Grep every page and finds rss, atom, opml feeds.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        GrepPlugin.__init__(self)
        self._feed_types = {'rss': 'RSS',  # <rss version="...">
                            'feed': 'OPML',  # <feed version="..."
                            'opml': 'OPML'  # <opml version="...">
                            }
        
        # Compile the XPATH
        self._tag_xpath = etree.XPath('//rss | //feed | //opml')

    def grep(self, request, response):
        """
        Plugin entry point, find feeds.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        dom = response.get_dom()
        uri = response.get_uri()

        # In some strange cases, we fail to normalize the document
        if dom is None:
            return

        # Find all feed tags
        element_list = self._tag_xpath(dom)

        for element in element_list:

            feed_tag = element.tag
            feed_type = self._feed_types[feed_tag.lower()]
            version = element.attrib.get('version', 'unknown')

            fmt = 'The URL "%s" is a %s version %s feed.'
            desc = fmt % (uri, feed_type, version)
            i = Info('Content feed resource', desc, response.id,
                     self.get_name())
            i.set_uri(uri)
            i.add_to_highlight(feed_type)
            
            self.kb_append_uniq(self, 'feeds', i, 'URL')

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page and finds rss, atom, opml feeds on them.
        This may be usefull for determining the feed generator and with that,
        the framework being used. Also this will be helpful for testing feed
        injection.
        """
