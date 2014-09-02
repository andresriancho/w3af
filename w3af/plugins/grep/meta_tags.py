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
    <meta name="verify-v1" content="/JBoXnwT1d7TbbWCwL8tXe+Ts2I2...0g7kdY=" />

    Answer:
    That's one of the verification elements used by Google Sitemaps. When you
    sign up for Sitemaps you have to add that element to a root page to
    demonstrate to Google that you're the site owner. So there is probably a
    Sitemaps account for the site, if you haven't found it already.
    """

    ATTR_NAME = 'name'
    ATTR_VALUE = 'value'

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
            for attr_name, attr_value in tag.items():

                for word in self.INTERESTING_WORDS:

                    # Check if we have something interesting
                    # and WHERE that thing actually is
                    where = content = None
                    if word in attr_name:
                        where = self.ATTR_NAME
                        content = attr_name
                    elif word in attr_value:
                        where = self.ATTR_VALUE
                        content = attr_value

                    # Now... if we found something, report it =)
                    if self._should_report(attr_name, attr_value, where):

                        # The attribute is interesting!
                        fmt = 'The URI: "%s" sent a <meta> tag with attribute'\
                              ' %s set to "%s" which looks interesting.'
                        desc = fmt % (response.get_uri(), where, content)

                        tag_name = self._find_name(tag)
                        if self.INTERESTING_WORDS.get(tag_name, None):
                            usage = self.INTERESTING_WORDS[tag_name]
                            desc += ' The tag is used for %s.' % usage
                        
                        i = Info('Interesting META tag', desc, response.id,
                                 self.get_name())
                        i.set_uri(response.get_uri())
                        i.add_to_highlight(where, content)

                        self.kb_append_uniq(self, 'meta_tags', i, 'URL')

    def _should_report(self, key, value, where):
        """
        :param key: The meta tag attribute name
        :param value: The meta tag attribute value
        :param where: The location (key|value) that we found interesting
        :return: True if we should report this information
        """
        if where is None:
            return False

        return True

    def _find_name(self, tag):
        """
        :return: the tag name.
        """
        for key, value in tag.items():
            if key.lower() == 'name':
                return value
        return None

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page for interesting meta tags. Some interesting
        meta tags are the ones that contain : 'microsoft', 'visual', 'linux' .
        """
