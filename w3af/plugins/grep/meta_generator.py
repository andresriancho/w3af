"""
meta_generator.py

Copyright 2019 Andres Riancho

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
from w3af.core.data.kb.info import Info
from w3af.core.data.kb.info_set import InfoSet


class meta_generator(GrepPlugin):
    """
    Use the <meta name="generator" content="..."> tags to get the site generator

    :author: Jose Nazario (jose@monkey.org)
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

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

        for generator in self._get_generators(response):
            self._save_to_kb(request, response, generator)

    def _save_to_kb(self, request, response, generator):
        desc = 'Found generator meta tag value: "%s"' % generator

        info = Info('Generator information', desc, response.id, self.get_name())
        info.set_uri(response.get_uri())
        info.add_to_highlight(generator)
        info[MetaTagsInfoSet.ITAG] = generator

        self.kb_append_uniq_group(self,
                                  'content_generator',
                                  info,
                                  group_klass=MetaTagsInfoSet)

    def _get_generators(self, response):
        """
        :param response: The HTTP response
        :return: A set with all generators
        """
        generators = set()

        for tag in parser_cache.dpc.get_tags_by_filter(response, ('meta',)):
            # pylint: disable=E1101
            name_attr_val = tag.attrib.get('name', None)
            # pylint: enable=E1101

            if name_attr_val is None:
                continue

            if 'generator' != name_attr_val.lower():
                continue

            # pylint: disable=E1101
            content_attr_val = tag.attrib.get('content', None)
            # pylint: enable=E1101

            if not content_attr_val:
                continue

            generators.add(content_attr_val)

        return generators

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin inspects pages looking for the meta generator value, 
        often used by CMS frameworks to identify their software and version.
        """


class MetaTagsInfoSet(InfoSet):

    ITAG = 'generator'

    TEMPLATE = (
        'The application returned {{ uris | length }} HTTP responses containing'
        ' the generator meta tag value "{{ generator }}". The first ten URLs '
        ' that match are:\n'
        ''
        '{% for url in uris[:10] %}'
        ' - {{ url }}\n'
        '{% endfor %}'
    )
