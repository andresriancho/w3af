"""
meta_generator.py

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

from .meta_tags import MetaTagsInfoSet

class meta_generator(GrepPlugin):    
    def __init__(self):
        GrepPlugin.__init__(self)
    
    """
    Use the <meta name="generator" content="X"> tage to get the site code.
    Often used by CMS systems like Wordpress or Joomla

    :author: Jose Nazario (jose@monkey.org)
    """
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

                if not attr_name or not attr_value:
                    # https://github.com/andresriancho/w3af/issues/2012
                    continue
                
                if attr_name == "name" and attr_value == "generator":
                    where = 'content'
                    content = tag.get('content', 'NOT FOUND')
                    desc = 'Found generator: "%s"' % content

                    i = Info('Generator information', desc, response.id,
                             self.get_name())
                    i.set_uri(response.get_uri())
                    i.add_to_highlight(where, content)
                    i['content'] = content
                    i['where'] = where

                    self.kb_append_uniq_group(self, 'content_generator', i,
                                              group_klass=MetaTagsInfoSet)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin inspects pages looking for the meta generator value, 
        often used by CMS frameworks to identify their software and version.
        """
