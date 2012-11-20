'''
hash_analysis.py

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
import re

import core.data.kb.knowledge_base as kb
import core.data.kb.info as info

from core.controllers.plugins.grep_plugin import GrepPlugin
from core.data.bloomfilter.scalable_bloom import ScalableBloomFilter


class hash_analysis(GrepPlugin):
    '''
    Identify hashes in HTTP responses.

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        GrepPlugin.__init__(self)

        self._already_reported = ScalableBloomFilter()

        # regex to split between words
        self._split_re = re.compile('[^\w]')

    def grep(self, request, response):
        '''
        Plugin entry point, identify hashes in the HTTP response.

        @param request: The HTTP request object.
        @param response: The HTTP response object
        @return: None
        '''
        # I know that by doing this I loose the chance of finding hashes in PDF files, but...
        # This is much faster
        if response.is_text_or_html():

            body = response.get_body()
            splitted_body = self._split_re.split(body)
            for possible_hash in splitted_body:

                #    This is a performance enhancement that cuts the execution
                #    time of this plugin in half.
                if len(possible_hash) > 31:

                    hash_type = self._get_hash_type(possible_hash)
                    if hash_type:

                        possible_hash = possible_hash.lower()
                        if self._has_hash_distribution(possible_hash):
                            if (possible_hash, response.get_url()) not in self._already_reported:
                                i = info.info()
                                i.set_plugin_name(self.get_name())
                                i.set_name(hash_type + 'hash in HTML content')
                                i.set_url(response.get_url())
                                i.add_to_highlight(possible_hash)
                                i.set_id(response.id)
                                msg = 'The URL: "' + response.get_url(
                                ) + '" returned a response that may'
                                msg += ' contain a "' + hash_type + \
                                    '" hash. The hash is: "' + possible_hash
                                msg += '". This is uncommon and requires human verification.'
                                i.set_desc(msg)
                                kb.kb.append(self, 'hash_analysis', i)

                                self._already_reported.add(
                                    (possible_hash, response.get_url()))

    def _has_hash_distribution(self, possible_hash):
        '''
        @param possible_hash: A string that may be a hash.
        @return: True if the possible_hash has an equal (aprox.) distribution
        of numbers and letters and only has hex characters (0-9, a-f)
        '''
        numbers = 0
        letters = 0
        for char in possible_hash:
            if char.isdigit():
                numbers += 1
            elif char in 'abcdef':
                letters += 1
            else:
                return False

        if numbers in range(letters - len(possible_hash) / 2, letters + len(possible_hash) / 2):
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
        '''
        @param possible_hash: A string that may be a hash.
        @return: The hash type if the string seems to be a md5 / sha1 hash.
        None otherwise.
        '''
        # FIXME: Add more here!
        if len(possible_hash) == 32:
            return 'MD5'
        elif len(possible_hash) == 40:
            return 'SHA1'
        else:
            return None

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.print_uniq(kb.kb.get('hash_analysis', 'hash_analysis'), None)

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin identifies hashes in HTTP responses.
        '''
