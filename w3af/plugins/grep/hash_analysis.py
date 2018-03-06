"""
hash_analysis.py

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
import re

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.info import Info


class hash_analysis(GrepPlugin):
    """
    Identify hashes in HTTP responses.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        GrepPlugin.__init__(self)

        self._already_reported = ScalableBloomFilter()

        # regex to split between words
        self._split_re = re.compile('[^\w]')

    def grep(self, request, response):
        """
        Plugin entry point, identify hashes in the HTTP response.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None
        """
        # I know that by doing this I loose the chance of finding hashes in
        # PDF files, but... this is much faster
        if not response.is_text_or_html():
            return

        body = response.get_body()
        splitted_body = self._split_re.split(body)
        for possible_hash in splitted_body:

            #    This is a performance enhancement that cuts the execution
            #    time of this plugin in half.
            if len(possible_hash) < 31 or\
            len(possible_hash) > 129 :
                return
            
            hash_type = self._get_hash_type(possible_hash)
            if not hash_type:
                return

            possible_hash = possible_hash.lower()
            if self._has_hash_distribution(possible_hash):
                if (possible_hash, response.get_url()) not in self._already_reported:
                    desc = 'The URL: "%s" returned a response that may contain'\
                          ' a "%s" hash. The hash string is: "%s". This is'\
                          ' uncommon and requires human verification.'
                    desc = desc % (response.get_url(), hash_type, possible_hash)
                    
                    i = Info('Hash string in HTML content', desc,
                             response.id, self.get_name())
                    i.set_url(response.get_url())
                    i.add_to_highlight(possible_hash)
                    
                    self.kb_append(self, 'hash_analysis', i)

                    self._already_reported.add( (possible_hash,
                                                 response.get_url()) )

    def _has_hash_distribution(self, possible_hash):
        """
        :param possible_hash: A string that may be a hash.
        :return: True if the possible_hash has an equal (aprox.) distribution
        of numbers and letters and only has hex characters (0-9, a-f)
        """
        numbers = 0
        letters = 0
        for char in possible_hash:
            if char.isdigit():
                numbers += 1
            elif char in 'abcdef':
                letters += 1
            else:
                return False

        low = letters - len(possible_hash) / 2
        high = letters + len(possible_hash) / 2
        if low < numbers < high:
            # Seems to be a hash, let's make a final test to avoid false positives with
            # strings like:
            # 2222222222222222222aaaaaaaaaaaaa
            is_hash = True
            for char in possible_hash:
                if possible_hash.count(char) > len(possible_hash) / 5:
                    is_hash = False
                    break
            return is_hash

        else:
            return False

    def _get_hash_type(self, possible_hash):
        """
        :param possible_hash: A string that may be a hash.
        :return: The hash type if the string seems to be a md5 / sha1 hash.
        None otherwise.
        """
        # When adding something here, please review the code above where
        # we also check the length.
        hash_type_len = {
                         'MD5': 32,
                         'SHA1': 40,
                         'SHA224': 56,
                         'SHA256': 64,
                         'SHA384': 96,
                         'SHA512': 128,
                         }
        for hash_type, hash_len in hash_type_len.items():                
            if len(possible_hash) == hash_len:
                return hash_type
            
        return None

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin identifies hashes in HTTP responses.
        """
