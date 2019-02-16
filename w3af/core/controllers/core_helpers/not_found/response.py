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
    __slots__ = ('_http_response',
                 '_clean_body',
                 'doc_type',
                 'normalized_path',
                 'url',
                 'diff',
                 'diff_with_id',
                 'id',
                 'code')

    def __init__(self, http_response):
        self._http_response = http_response
        self._clean_body = None

        self.normalized_path = self.normalize_path(http_response.get_url())
        self.doc_type = http_response.doc_type
        self.url = http_response.get_url().url_string
        self.id = http_response.id
        self.code = http_response.get_code()

        # These two are used in _handle_large_http_responses()
        self.diff = None
        self.diff_with_id = None

    @property
    def body(self):
        if self._clean_body is not None:
            return self._clean_body

        self._clean_body = get_clean_body(self._http_response)
        self._http_response = None
        return self._clean_body

    @staticmethod
    def normalize_path(url):
        """
        Normalizes a path. Examples:

            * /abc/def.html -> /abc/filename.html
            * /abc/def      -> /abc/filename
            * /abc/         -> /path/
            * /abc/def/     -> /abc/path/
            * /abc/def/x.do -> /abc/def/filename.do
            * /abc?id=1     -> /filename
            * /?id=1        -> /

        :return: The normalized path
        """
        url = url.copy()
        url.set_querystring('')

        path = url.get_path()

        if path == '/':
            return url.url_string

        filename = url.get_file_name()

        if not filename:
            relative_url = '../path/'
            url = url.url_join(relative_url)
            return url.url_string

        extension = url.get_extension()
        if extension:
            filename = 'filename.%s' % extension
        else:
            filename = 'filename'

        url.set_file_name(filename)
        return url.url_string

    def __repr__(self):
        return '<FourOhFourResponse (url:%s, code:%s)>' % (self.url, self.code)
