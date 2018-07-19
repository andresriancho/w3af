"""
url_session.py

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
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.constants.cookies import ALL_COOKIES
from w3af.core.data.kb.info import Info


class url_session(GrepPlugin):
    """
    Finds URLs which have a parameter that holds the session ID. 

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    
    SESSID_PARAMS = ALL_COOKIES
    
    def __init__(self):
        GrepPlugin.__init__(self)
        self._already_reported = ScalableBloomFilter()

    def grep(self, request, response):
        """
        Plugin entry point, find the blank bodies and report them.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        self.analyze_uri(request, response)
        self.analyze_document_links(request, response)
    
    def _has_sessid(self, uri):
        """
        :return: A set which contains the session ID parameters (if any)
        """
        sessid_in_uri = set()
        if uri.has_query_string():
            query_string = uri.get_querystring()
            params = set(query_string.keys())
            sessid_in_uri = self.SESSID_PARAMS.intersection(params)
        return sessid_in_uri
        
    def analyze_document_links(self, request, response):
        """
        Find session IDs in the URI and store them in the KB.
        """
        try:
            doc_parser = parser_cache.dpc.get_document_parser_for(response)
        except:
            pass
        else:
            parsed_refs, _ = doc_parser.get_references()
            
            for link_uri in parsed_refs:
                if self._has_sessid(link_uri) and \
                response.get_url() not in self._already_reported:
                    #   report these informations only once
                    self._already_reported.add(response.get_url())

                    desc = 'The HTML content at "%s" contains a link (%s)'\
                           ' which holds a session id. The ID could be leaked'\
                           ' to third party domains through the referrer'\
                           ' header.'
                    desc = desc % (response.get_url(), link_uri)
                    
                    #   append the info object to the KB.
                    i = Info('Session ID in URL', desc, response.id,
                             self.get_name())
                    i.set_uri(response.get_uri())
                    
                    self.kb_append(self, 'url_session', i)
                    break

    def analyze_uri(self, request, response):
        """
        Find session IDs in the URI and store them in the KB.
        """
        request_uri = request.get_uri()
        if self._has_sessid(request_uri) and \
        response.get_url() not in self._already_reported:
                #   report these informations only once
                self._already_reported.add(response.get_url())
                
                desc = 'The URL "%s" contains a session id which could be'\
                       ' leaked to third party domains through the referrer'\
                       ' header.'
                desc %= request_uri
                
                #   append the info object to the KB.
                i = Info('Session ID in URL', desc, response.id,
                         self.get_name())
                i.set_uri(response.get_uri())

                self.kb_append(self, 'url_session', i)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds URLs which contain a parameter that stores the
        session ID.
        
        This configuration leaves the session id exposed in browser
        and server logs, and is also leaked through the HTTP referrer
        header.
        """
