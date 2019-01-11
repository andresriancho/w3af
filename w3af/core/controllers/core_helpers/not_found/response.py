"""
response.py

Copyright 2018 Andres Riancho

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
from w3af.core.controllers.core_helpers.not_found.get_clean_body import get_clean_body


class FourOhFourResponse(object):
    __slots__ = ('body',
                 'doc_type',
                 'path',
                 'normalized_path',
                 'url',
                 'diff',
                 'diff_with_id',
                 'id',
                 'code')

    def __init__(self, http_response):
        self.body = get_clean_body(http_response)
        self.doc_type = http_response.doc_type
        self.path = http_response.get_url().get_domain_path().url_string
        self.normalized_path = FourOhFourResponse.normalize_path(http_response.get_url())
        self.url = http_response.get_url().url_string
        self.id = http_response.id
        self.code = http_response.get_code()

        # These two are used in _handle_large_http_responses()
        self.diff = None
        self.diff_with_id = None

    @staticmethod
    def normalize_path(url):
        """
        Normalizes a path. Examples:

            * /abc/def.html -> /abc/filename.html
            * /abc/def      -> /abc/filename
            * /abc/         -> /path/
            * /abc/def/     -> /abc/path/
            * /abc/def/x.do -> /abc/def/filename.do

        :return: The normalized path
        """
        filename = url.get_file_name()
        path = url.get_path()

        if path == '/':
            return url.url_string

        if not filename:
            relative_url = '../path/'
            url = url.url_join(relative_url)
            return url.url_string

        extension = url.get_extension()
        if extension:
            filename = 'filename.%s' % extension
        else:
            filename = 'filename'

        url = url.copy()
        url.set_file_name(filename)
        return url.url_string

    def __repr__(self):
        return '<FourOhFourResponse (url:%s, code:%s)>' % (self.url, self.code)
