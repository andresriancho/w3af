"""
cache_control.py

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
from collections import namedtuple

import w3af.core.data.constants.severity as severity
import w3af.core.data.parsers.parser_cache as parser_cache

from w3af.core.data.db.disk_list import DiskList
from w3af.core.data.kb.vuln import Vuln
from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404


CacheSettings = namedtuple('CacheSettings', ['type', 'value'])


class cache_control(GrepPlugin):
    """
    Grep every page for Pragma and Cache-Control headers.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    
    SAFE_CONFIG = {'pragma': 'no-cache',
                   'cache-control': 'no-store'}
    
    def __init__(self):
        GrepPlugin.__init__(self)

        self._total_count = 0
        self._vuln_count = 0
        self._vulns = DiskList(table_prefix='cache_control')
        self._ids = DiskList(table_prefix='cache_control')

    def grep(self, request, response):
        if response.is_image() or response.is_swf():
            return

        if response.get_url().get_protocol() == 'http':
            return

        if 300 < response.get_code() < 310:
            return
        
        if response.body == '':
            return

        if is_404(response):
            return

        self._total_count += 1

        cache_control_settings = self._get_cache_control(response)
        self._analyze_cache_control(cache_control_settings, response)
    
    def _get_cache_control(self, response):
        """
        :param response: The http response we want to extract the information
                         from.
        :return: A list with the headers and meta tag information used to
                 configure the browser cache control.
        """
        res = []

        cache_control_headers = self.SAFE_CONFIG.keys()
        headers = response.get_headers()
        
        for _type in cache_control_headers:
            header_value, _ = headers.iget(_type, None)
            if header_value is not None:
                res.append(CacheSettings(_type, header_value.lower()))
                
        try:
            doc_parser = parser_cache.dpc.get_document_parser_for(response)
        except BaseFrameworkException:
            pass
        else:
            for meta_tag in doc_parser.get_meta_tags():
                header_name = meta_tag.get('http-equiv', None)
                header_value = meta_tag.get('content', None)
                if header_name is not None and header_value is not None:
                    header_name = header_name.lower()
                    header_value = header_value.lower()
                    if header_name in cache_control_headers:
                        res.append(CacheSettings(header_name, header_value))
        
        return res

    def _analyze_cache_control(self, cache_control_settings, response):
        """
        Analyze the cache control settings set in headers and meta tags,
        store the information to report the vulnerabilities.
        """
        received_headers = set()
        
        for cache_setting in cache_control_settings:
            expected_header = self.SAFE_CONFIG[cache_setting.type]
            received_header = cache_setting.value.lower()
            received_headers.add(cache_setting.type)
            if expected_header not in received_header:
                # The header has an incorrect value
                self.is_vuln(response)
                return
        
        if len(received_headers) != len(self.SAFE_CONFIG):
            # No cache control header found
            self.is_vuln(response)
    
    def is_vuln(self, response):
        self._vuln_count += 1
        if response.get_url() not in self._vulns:
            self._vulns.append(response.get_url())
            self._ids.append(response.id)
    
    def end(self):
        # If all URLs implement protection, don't report anything.
        if not self._vuln_count:
            return

        # If none of the URLs implement protection, simply report
        # ONE vulnerability that says that.
        if self._total_count == self._vuln_count:
            desc = ('The whole target web application has no protection (Pragma'
                    ' and Cache-Control headers) against sensitive content'
                    ' caching.')
            
        # If most of the URLs implement the protection but some
        # don't, report ONE vulnerability saying: "Most are protected, but x, y
        # are not.
        if self._total_count > self._vuln_count:
            desc = ('Some URLs have no protection (Pragma and Cache-Control'
                    ' headers) against sensitive content caching. Among them:\n')
            desc += ' '.join([str(url) + '\n' for url in self._vulns])
        
        response_ids = [_id for _id in self._ids]
        
        v = Vuln('Missing cache control for HTTPS content', desc,
                 severity.LOW, response_ids, self.get_name())
        
        self.kb_append_uniq(self, 'cache_control', v, 'URL')
        
        self._vulns.cleanup()
        self._ids.cleanup()

    def get_long_desc(self):
        return """
        This plugin analyzes every HTTPS response and reports instances of
        incorrect cache control which might lead the user's browser to cache
        sensitive contents on their system.
        
        The expected headers for HTTPS responses are:
            - Pragma: No-cache
            - Cache-control: No-store
        """
