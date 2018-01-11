"""
swf.py

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
import zlib

from w3af.core.data.parsers.doc.baseparser import BaseParser
from w3af.core.data.parsers.utils.re_extract import ReExtract


class SWFParser(BaseParser):
    """
    This class is a SWF (flash) parser which just focuses on extracting URLs.
    
    The parser is based on "SWF File Format Specification Version 10"
    http://www.adobe.com/content/dam/Adobe/en/devnet/swf/pdf/swf_file_format_spec_v10.pdf

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, http_response):
        BaseParser.__init__(self, http_response)

        self._re_urls = set()

    @staticmethod
    def can_parse(http_resp):
        """
        :return: True if the http_resp contains a SWF file.
        """
        if http_resp.content_type != 'application/x-shockwave-flash':
            return False

        body = http_resp.get_body()

        if len(body) > 5:
            magic = body[:3]

            # TODO: Add more checks here?
            if magic in ('FWS', 'CWS'):
                return True

        return False

    def _is_compressed(self, swf_document):
        """

        :param swf_content: The SWF file.
        :return: True if the SWF is compressed
        """
        return swf_document.startswith('CWS')

    def _inflate(self, swf_document):
        """
        zlib.inflate the SWF file.

        :param swf_content: The SWF file.
        :return: A decompressed version of the SWF
        """
        compressed_data = swf_document[8:]
        try:
            uncompressed_data = zlib.decompress(compressed_data)
        except zlib.error, e:
            raise ValueError('Failed to inflate: ' + str(e))
        else:
            # TODO: Strings in SWF are NULL-Byte delimited. Maybe we can
            # use that to extract strings and apply regular expressions
            # more carefully?
            return uncompressed_data

    def parse(self):
        """
        Parse the SWF bytecode.
        For now... don't decompile anything, just apply regular
        expressions to it.
        """
        swf_body = self.get_http_response().get_body()

        if self._is_compressed(swf_body):
            try:
                swf_body = self._inflate(swf_body)
            except Exception:
                # If the inflate fails... there is nothing else to do.
                return

        self._0x83_getURL_parse(swf_body)
        self._re_extract(swf_body)

    def _re_extract(self, swf_body):
        """
        Get the URLs using a regex
        """
        re_extract = ReExtract(swf_body, self._base_url, self._encoding)
        re_extract.parse()
        self._re_urls.update(re_extract.get_references())

    def _0x83_getURL_parse(self, swf_body):
        """
        After reading a couple of SWF files with a hex editor it was possible
        to identify the following pattern:
        
            0x83    0xLENGTH    0x00    (0xLENGTH - 2 chars)    0x00
        
        0x83 is the bytecode for Adobe's getURL
        0xLENGTH is the string length of the first parameter including the two
                 0x00 string delimiters.
        
        So, with this information I'll extract links!
        
        :return: Store new URLs in self._re_urls, None is returned.
        """
        for index, char in enumerate(swf_body):
            if char == '\x83':
                try:
                    plus_two_zero = swf_body[index+2] == '\x00'
                except IndexError:
                    continue
                else:
                    if not plus_two_zero:
                        continue

                # potential getURL with string as first parameter
                # lets get the length and verify that there is a 0x00 where
                # we expect it to be
                str_len = ord(swf_body[index+1])

                try:
                    str_end = swf_body[index + 1 + str_len]
                except IndexError:
                    # The str_len was too long and took us out of the string
                    # length, this is a "common" bug since our parser is not
                    # very smart
                    #
                    # https://github.com/andresriancho/w3af/issues/5535
                    continue

                # Strings in SWF bytecode have 0x00 content 0x00 and the len
                # counts the delimiters, so a length of 2 or less is useless
                if str_len <= 2:
                    continue
                
                if str_end == '\x00':
                    # Getting closer... lets reduce more false positives by
                    # verifying that all chars in the url are ASCII
                    start = index + 3
                    end = start + str_len - 2
                    url_str = swf_body[start:end]
                    
                    if all(32 < ord(c) < 127 for c in url_str):
                        # All chars are ASCII, we've got a URL!
                        #
                        # In case you're wondering, this url_join does work with
                        # both relative and full URLs
                        try:
                            url = self._base_url.url_join(url_str)
                        except ValueError:
                            # Handle cases like "javascript:foo(1)" URLs
                            # https://github.com/andresriancho/w3af/issues/2091
                            pass
                        else:
                            self._re_urls.add(url)

    def get_clear_text_body(self):
        return u''

    def get_references(self):
        """
        Searches for references on a page. w3af searches references in every
        html tag, including:
            - a
            - forms
            - images
            - frames
            - etc.

        :return: Two lists, one with the parsed URLs, and one with the URLs
                 that came out of a regular expression. The second list if less
                 trustworthy.
        """
        return [], list(self._re_urls)

    get_references_of_tag = get_forms = BaseParser._return_empty_list
    get_comments = BaseParser._return_empty_list
    get_meta_redir = get_meta_tags = get_emails = BaseParser._return_empty_list

