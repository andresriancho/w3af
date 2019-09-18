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
import w3af.core.data.parsers.parser_cache as parser_cache

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.info import Info


class feeds(GrepPlugin):
    """
    Grep every page and finds rss, atom, opml feeds.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    TAGS = ('rss', 'feed', 'opml')

    def __init__(self):
        GrepPlugin.__init__(self)
        self._feed_types = {'rss': 'RSS',  # <rss version="...">
                            'feed': 'OPML',  # <feed version="..."
                            'opml': 'OPML'  # <opml version="...">
                            }

    def grep(self, request, response):
        """
        Plugin entry point, find feeds.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        uri = response.get_uri()

        for tag in parser_cache.dpc.get_tags_by_filter(response, self.TAGS):
            # pylint: disable=E1101
            feed_tag = tag.name
            version = tag.attrib.get('version', 'unknown')
            # pylint: disable=E1101
            feed_type = self._feed_types[feed_tag.lower()]

            desc = 'The URL "%s" is a %s version %s feed.'
            desc %= (uri, feed_type, version)

            i = Info('Content feed resource', desc, response.id, self.get_name())
            i.set_uri(uri)
            i.add_to_highlight(feed_type)
            
            self.kb_append_uniq(self, 'feeds', i, 'URL')

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page and finds rss, atom, opml feeds on them.
        This may be useful for determining the feed generator and with that,
        the framework being used. Also this will be helpful for testing feed
        injection.
        """
