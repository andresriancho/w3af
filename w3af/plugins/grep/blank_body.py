"""
blank_body.py

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
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.info import Info


class blank_body(GrepPlugin):
    """
    Find responses with empty body.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    METHODS = ('GET', 'POST')
    HTTP_CODES = (401, 304, 302, 301, 204, 405)
    
    def __init__(self):
        GrepPlugin.__init__(self)
        self.already_reported = ScalableBloomFilter()

    def grep(self, request, response):
        """
        Plugin entry point, find the blank bodies and report them.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        if response.get_body() == '' and request.get_method() in self.METHODS\
        and response.get_code() not in self.HTTP_CODES\
        and not response.get_headers().icontains('location')\
        and response.get_url().uri2url() not in self.already_reported:

            self.already_reported.add(response.get_url().uri2url())

            desc = 'The URL: "%s" returned an empty body, this could indicate'\
                   ' an application error.'
            desc %= response.get_url()

            i = Info('Blank http response body', desc, response.id,
                     self.get_name())
            i.set_url(response.get_url())
            
            self.kb_append(self, 'blank_body', i)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds HTTP responses with a blank body, these responses may
        indicate errors or misconfigurations in the web application or the web
        server.
        """
