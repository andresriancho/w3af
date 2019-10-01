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
from w3af.core.data.kb.info_set import InfoSet
from w3af.core.data.kb.info import Info

ATTR_NAME = 'name'
ATTR_VALUE = 'value'
CONTENT = 'content'
WHERE = 'where'


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
    INTERESTING_WORDS = {'user': None,
                         'pass': None,
                         'microsoft': None,
                         'visual': None,
                         'linux': None,
                         'source': None,
                         'author': None,
                         'release': None,
                         'version': None,
                         'verify-v1': 'Google Sitemap'}

    def grep(self, request, response):
        """
        Plugin entry point, search for meta tags.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        if not response.is_text_or_html():
            return

        if is_404(response):
            return

        try:
            dp = parser_cache.dpc.get_document_parser_for(response)
        except BaseFrameworkException:
            return

        meta_tag_list = dp.get_meta_tags()

        for tag in meta_tag_list:
            for attr_name, attr_value in tag.items():

                if not attr_name or not attr_value:
                    # https://github.com/andresriancho/w3af/issues/2012
                    continue

                for word in self.INTERESTING_WORDS:

                    # Check if we have something interesting and WHERE that
                    # thing actually is
                    if word in attr_name:
                        where = ATTR_NAME
                        content = attr_name
                    elif word in attr_value:
                        where = ATTR_VALUE
                        content = attr_value
                    else:
                        # Go to the next one if nothing is found
                        continue

                    # Now... if we found something, report it =)
                    desc = ('The URI: "%s" sent a <meta> tag with the attribute'
                            ' %s set to "%s" which looks interesting.')
                    desc %= (response.get_uri(), where, content)

                    tag_name = self._find_tag_name(tag)
                    usage = self.INTERESTING_WORDS.get(tag_name, None)
                    if usage is not None:
                        desc += ' The tag is used for %s.' % usage

                    i = Info('Interesting META tag', desc, response.id,
                             self.get_name())
                    i.set_uri(response.get_uri())
                    i.add_to_highlight(where, content)
                    i[CONTENT] = content
                    i[WHERE] = where

                    self.kb_append_uniq_group(self, 'meta_tags', i,
                                              group_klass=MetaTagsInfoSet)

    def _find_tag_name(self, tag):
        """
        :return: the tag name.
        """
        for key, value in tag.items():
            if key.lower() == 'name':
                return value.lower()
        return None

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page for interesting meta tags. Some interesting
        meta tags are the ones that contain : 'microsoft', 'visual', 'linux' .
        """


class MetaTagsInfoSet(InfoSet):
    ITAG = CONTENT
    TEMPLATE = (
        'The application sent a <meta> tag with the attribute {{ where }} set'
        ' to "{{ content }}" which looks interesting and should be manually'
        ' reviewed. The first ten URLs which sent the tag are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )
