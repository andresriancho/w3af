'''
feeds.py

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
from lxml import etree

import core.data.kb.knowledge_base as kb
import core.data.kb.info as info

from core.controllers.plugins.grep_plugin import GrepPlugin
from core.data.bloomfilter.scalable_bloom import ScalableBloomFilter


class feeds(GrepPlugin):
    '''
    Grep every page and finds rss, atom, opml feeds.

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        GrepPlugin.__init__(self)
        self._feed_types = {'rss': 'RSS',  # <rss version="...">
                            'feed': 'OPML',  # <feed version="..."
                            'opml': 'OPML'  # <opml version="...">
                            }
        self._already_inspected = ScalableBloomFilter()

        # Compile the XPATH
        self._tag_xpath = etree.XPath('//rss | //feed | //opml')

    def grep(self, request, response):
        '''
        Plugin entry point, find feeds.

        @param request: The HTTP request object.
        @param response: The HTTP response object
        @return: None
        '''
        dom = response.getDOM()
        uri = response.getURI()

        # In some strange cases, we fail to normalize the document
        if uri not in self._already_inspected and dom is not None:

            self._already_inspected.add(uri)

            # Find all feed tags
            element_list = self._tag_xpath(dom)

            for element in element_list:

                feed_tag = element.tag
                feed_type = self._feed_types[feed_tag.lower()]
                version = element.attrib.get('version', 'unknown')

                i = info.info()
                i.set_plugin_name(self.get_name())
                i.set_name(feed_type + ' feed')
                i.setURI(uri)
                fmt = 'The URL "%s" is a %s version %s feed.'
                msg = fmt % (uri, feed_type, version)
                i.set_desc(msg)
                i.set_id(response.id)
                i.addToHighlight(feed_type)
                kb.kb.append(self, 'feeds', i)

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.print_uniq(kb.kb.get('feeds', 'feeds'), 'URL')

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin greps every page and finds rss, atom, opml feeds on them.
        This may be usefull for determining the feed generator and with that,
        the framework being used. Also this will be helpful for testing feed
        injection.
        '''
