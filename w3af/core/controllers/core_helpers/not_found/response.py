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
import msgpack

from w3af.core.controllers.core_helpers.not_found.get_clean_body import get_clean_body


class FourOhFourResponse(object):
    __slots__ = ('_http_response',
                 '_clean_body',
                 'content_type',
                 'normalized_path',
                 'url',
                 'diff',
                 'diff_with_id',
                 'id',
                 'code')

    def __init__(self,
                 http_response=None,
                 clean_body=None,
                 normalized_path=None,
                 content_type=None,
                 url=None,
                 _id=None,
                 code=None,
                 diff=None,
                 diff_with_id=None):

        self._http_response = http_response
        self._clean_body = clean_body

        self.normalized_path = normalized_path
        self.content_type = content_type
        self.url = url
        self.id = _id
        self.code = code

        # These two are used in _handle_large_http_responses()
        self.diff = diff
        self.diff_with_id = diff_with_id

    @classmethod
    def from_http_response(cls, http_response):
        normalized_path = FourOhFourResponse.normalize_path(http_response.get_url())

        return cls(http_response=http_response,
                   clean_body=None,
                   normalized_path=normalized_path,
                   content_type=http_response.content_type,
                   url=http_response.get_url().url_string,
                   _id=http_response.id,
                   code=http_response.get_code(),
                   diff=None,
                   diff_with_id=None)

    @property
    def body(self):
        if self._clean_body is not None:
            return self._clean_body

        self._clean_body = get_clean_body(self._http_response)
        self._http_response = None
        return self._clean_body

    def __eq__(self, other):
        for attr in self.__slots__:
            if self.__getattribute__(attr) != other.__getattribute__(attr):
                return False

        return True

    def dumps(self):
        return msgpack.dumps(self.to_dict(),
                             use_bin_type=True)

    @classmethod
    def loads(cls, serialized_response):
        data = msgpack.loads(serialized_response, raw=False)
        return cls.from_dict(data)

    def to_dict(self):
        return {'clean_body': self.body,
                'content_type': self.content_type,
                'normalized_path': self.normalized_path,
                'url': self.url,
                'id': self.id,
                'code': self.code,
                'diff': self.diff,
                'diff_with_id': self.diff_with_id}

    @classmethod
    def from_dict(cls, response_as_dict):
        return cls(http_response=None,
                   clean_body=response_as_dict['clean_body'],
                   normalized_path=response_as_dict['normalized_path'],
                   content_type=response_as_dict['content_type'],
                   url=response_as_dict['url'],
                   _id=response_as_dict['id'],
                   code=response_as_dict['code'],
                   diff=response_as_dict['diff'],
                   diff_with_id=response_as_dict['diff_with_id'])

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
