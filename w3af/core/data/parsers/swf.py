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

from w3af.core.data.parsers.baseparser import BaseParser


class SWFParser(BaseParser):
    """
    This class is a SWF (flash) parser which just focuses on extracting URLs.
    
    The parser is based on "SWF File Format Specification Version 10"
    http://www.adobe.com/content/dam/Adobe/en/devnet/swf/pdf/swf_file_format_spec_v10.pdf

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, HTTPResponse):
        BaseParser.__init__(self, HTTPResponse)

        swf = HTTPResponse.get_body()
        if self._is_compressed(swf):
            try:
                swf = self._inflate(swf)
            except Exception:
                # If the inflate fails... there is nothing else to do.
                return

        self._parse(swf)

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
            raise Exception('Failed to inflate: ' + str(e))
        else:
            # TODO: Strings in SWF are NULL-Byte delimited. Maybe we can
            # use that to extract strings and apply regular expressions
            # more carefully?
            return uncompressed_data

    def _parse(self, swf_body):
        """
        Parse the SWF bytecode.
        For now... don't decompile anything, just apply regular
        expressions to it.

        :param swf_body: SWF bytecode string
        """
        self._regex_url_parse(swf_body)
        self._0x83_getURL_parse(swf_body)
    
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
            if char == '\x83' and swf_body[index+2] == '\x00':
                # potential getURL with string as first parameter
                # lets get the length and verify that there is a 0x00 where
                # we expect it to be
                str_len = ord(swf_body[index+1])
                str_end = swf_body[index + 1 + str_len]

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
                        url = self._base_url.url_join(url_str)
                        self._re_urls.add(url)

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
        return ([], list(self._re_urls))

    def _return_empty_list(self, *args, **kwds):
        """
        This method is called (see below) when the caller invokes one of:
            - get_forms
            - get_comments
            - get_meta_redir
            - get_meta_tags
            - get_references_of_tag

        :return: Because we are a PDF document, we don't have the same things that
        a nice HTML document has, so we simply return an empty list.
        """
        return []

    get_references_of_tag = get_forms = get_comments = _return_empty_list
    get_meta_redir = get_meta_tags = _return_empty_list

