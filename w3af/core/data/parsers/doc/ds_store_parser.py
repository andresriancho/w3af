"""
ds_store_parser.py

Copyright 2015 Andres Riancho

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

"""
import struct

from cStringIO import StringIO
from ds_store import DSStore
from ds_store.buddy import BuddyError

import w3af.core.controllers.output_manager as om

from w3af.core.data.parsers.doc.baseparser import BaseParser


class DSStoreParser(BaseParser):
    """
    Extracts URLs from .DS_Store files
    """

    def __init__(self, http_response):
        super(DSStoreParser, self).__init__(http_response)
        self._urls = set()

    def get_clear_text_body(self):
        return ''

    def get_references(self):
        return self._urls, []

    get_references_of_tag = get_forms = BaseParser._return_empty_list
    get_comments = BaseParser._return_empty_list
    get_meta_redir = get_meta_tags = get_emails = BaseParser._return_empty_list

    @staticmethod
    def can_parse(http_resp):
        """
        :param http_resp: A http response object that contains a document of
                          type HTML / PDF / WML / etc.

        :return: True if the document parameter is a string that contains a
                 .DS_Store document which we know how to parse.
        """
        if not http_resp.get_raw_body().startswith('\x00\x00\x00\x01Bud1'):
            return False

        try:
            parser = DSStoreParser(http_resp)
            parser.parse()
        except BuddyError:
            return False
        except KeyError:
            # https://bitbucket.org/al45tair/ds_store/issues/6/keyerror-udsdb
            return False
        else:
            extracted_urls, _ = parser.get_references()
            return bool(extracted_urls)

    def parse(self):
        """
        Extracts URLs from the DS_Store file
        :return: None, URLs are saved and need to be retrieved using the
                 get_references method
        """
        ds_store_file = StringIO(self.get_http_response().get_raw_body())

        try:
            store = DSStore.open(ds_store_file, 'r')
        except struct.error as se:
            msg = 'Unexpected exception found in DS_Store parser: "%s"'
            om.out.debug(msg % se)
            return

        if not store:
            return

        current_url = self._http_response.get_url()

        try:
            for entry in store:
                try:
                    self._urls.add(current_url.url_join(entry.filename))
                except ValueError:
                    # Many things might fail here when we join the filename with
                    # the current URL. Simply ignore for now.
                    continue
        except struct.error as se:
            msg = 'Unexpected exception found in DS_Store parser: "%s"'
            om.out.debug(msg % se)
            return
