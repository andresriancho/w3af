"""
strange_headers.py

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
import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.controllers.misc.group_by_min_key import group_by_min_key
from w3af.core.data.kb.info import Info


class strange_headers(GrepPlugin):
    """
    Grep headers for uncommon headers sent in HTTP responses.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    # Remember that this headers are only the ones SENT BY THE SERVER TO THE
    # CLIENT. Headers must be uppercase in order to compare them
    COMMON_HEADERS = set([
        "ACCEPT-RANGES",
        "AGE",
        "ALLOW",
        "CONNECTION",
        "CONTENT-ENCODING",
        "CONTENT-LENGTH",
        "CONTENT-TYPE",
        "CONTENT-LANGUAGE",
        "CONTENT-LOCATION",
        "CACHE-CONTROL",
        "DATE",
        "EXPIRES",
        "ETAG",
        "KEEP-ALIVE",
        "LAST-MODIFIED",
        "LOCATION",
        "PUBLIC",
        "PRAGMA",
        "PROXY-CONNECTION",
        "SET-COOKIE",
        "SERVER",
        "STRICT-TRANSPORT-SECURITY",
        "TRANSFER-ENCODING",
        "VIA",
        "VARY",
        "WWW-AUTHENTICATE",
        "X-FRAME-OPTIONS",
        "X-CONTENT-TYPE-OPTIONS",
        "X-POWERED-BY",
        "X-ASPNET-VERSION",
        "X-CACHE",
        "X-UA-COMPATIBLE",
        "X-PAD",
        "X-XSS-Protection"]
    )

    def __init__(self):
        GrepPlugin.__init__(self)

    def grep(self, request, response):
        """
        Plugin entry point.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, all results are saved in the kb.
        """
        # Check if the header names are common or not
        for header_name in response.get_headers().keys():
            if header_name.upper() not in self.COMMON_HEADERS:

                # Check if the kb already has a info object with this code:
                strange_header_infos = kb.kb.get('strange_headers',
                                                 'strange_headers')

                for info_obj in strange_header_infos:
                    if info_obj['header_name'] == header_name:
                        # Work with the "old" info object:
                        id_list = info_obj.get_id()
                        id_list.append(response.id)
                        info_obj.set_id(id_list)
                        break
                else:
                    # Create a new info object from scratch and save it to
                    # the kb:
                    hvalue = response.get_headers()[header_name]
                    
                    desc = 'The remote web server sent the HTTP header: "%s"'\
                           ' with value: "%s", which is quite uncommon and'\
                           ' requires manual analysis.'
                    desc = desc % (header_name, hvalue)

                    i = Info('Strange header', desc, response.id,
                             self.get_name())
                    i.set_url(response.get_url())
                    i['header_name'] = header_name
                    i['header_value'] = hvalue
                    i.add_to_highlight(hvalue, header_name)
                    
                    kb.kb.append(self, 'strange_headers', i)

        # Now check for protocol anomalies
        self._content_location_not_300(request, response)

    def _content_location_not_300(self, request, response):
        """
        Check if the response has a content-location header and the response code
        is not in the 300 range.

        :return: None, all results are saved in the kb.
        """
        if 'content-location' in response.get_lower_case_headers() \
        and response.get_code() > 300\
        and response.get_code() < 310:
            desc = 'The URL: "%s" sent the HTTP header: "content-location"'\
                   ' with value: "%s" in an HTTP response with code %s which'\
                   ' is a violation to the RFC.'
            desc = desc % (response.get_url(),
                           response.get_lower_case_headers()['content-location'],
                           response.get_code())
            i = Info('Content-Location HTTP header anomaly', desc,
                     response.id, self.get_name())
            i.set_url(response.get_url())
            i.add_to_highlight('content-location')
            
            kb.kb.append(self, 'anomaly', i)

    def end(self):
        """
        This method is called when the plugin wont be used anymore.
        """
        headers = kb.kb.get('strange_headers', 'strange_headers')
        # This is how I saved the data:
        #    i['header_name'] = header_name
        #    i['header_value'] = response.get_headers()[header_name]

        # Group correctly
        tmp = []
        for i in headers:
            tmp.append((i['header_name'], i.get_url()))

        # And don't print duplicates
        tmp = list(set(tmp))

        resDict, itemIndex = group_by_min_key(tmp)
        if itemIndex == 0:
            # Grouped by header_name
            msg = 'The header: "%s" was sent by these URLs:'
        else:
            # Grouped by URL
            msg = 'The URL: "%s" sent these strange headers:'

        for k in resDict:
            om.out.information(msg % k)
            for i in resDict[k]:
                om.out.information('- ' + i)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps all headers for non-common headers. This could be useful
        to identify special modules and features added to the server.
        """
