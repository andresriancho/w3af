"""
json.py

Copyright 2014 Andres Riancho

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
import json

from w3af.core.data.dc.generic.data_container import DataContainer
from w3af.core.data.dc.utils.filter_printable import filter_non_printable
from w3af.core.data.constants.encodings import UTF8
from w3af.core.data.dc.utils.json_iter_setters import (json_iter_setters,
                                                       json_complex_str,
                                                       MutableWrapper)

ERR_MSG = 'Unsupported data "%s" for json container.'


class JSONContainer(DataContainer):
    """
    This class represents a data container for json.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    JSON_CONTENT_TYPE = 'application/json'
    DEFAULT_HEADERS = {'Content-Type': JSON_CONTENT_TYPE}

    def __init__(self, json_post_data, headers=None, encoding=UTF8):
        """
        :param json_post_data: The JSON data as string
        :param headers: The headers as dict
        """
        DataContainer.__init__(self, encoding=encoding)

        if not isinstance(json_post_data, basestring):
            raise TypeError(ERR_MSG % json_post_data)

        if not JSONContainer.is_json(json_post_data):
            raise ValueError(ERR_MSG % json_post_data[:50])

        if headers is not None and not isinstance(headers, dict):
            raise TypeError(ERR_MSG % headers)

        self._json = None
        self._raw_json = None

        self._headers = headers
        if self._headers is None:
            self._headers = JSONContainer.DEFAULT_HEADERS.copy()

        self.parse_json(json_post_data)

    def __reduce__(self):
        return self.__class__, (self._raw_json, self._headers), {'token': self.token,
                                                                 'encoding': self.encoding}

    def get_type(self):
        return 'JSON'

    @staticmethod
    def content_type_matches(headers):
        content_type, _ = headers.iget('content-type', '')
        return 'json' in content_type.lower()

    @staticmethod
    def is_json(post_data):
        try:
            json.loads(post_data)
        except:
            return False
        else:
            return True

    @staticmethod
    def get_mutable_json(json_post_data):
        return MutableWrapper(json.loads(json_post_data))

    def parse_json(self, json_post_data):
        """
        Parses the json post data and stores all the information required to
        fuzz it as attributes.

        :param json_post_data: The JSON as a string
        :raises: ValueError if the json_post_data is not valid XML or XML-RPC
        """
        try:
            self._json = JSONContainer.get_mutable_json(json_post_data)
            self._raw_json = json_post_data
        except:
            raise ValueError(ERR_MSG % json_post_data[:50])

    @classmethod
    def from_postdata(cls, headers, post_data):
        if not JSONContainer.content_type_matches(headers):
            raise ValueError('Missing json content type.')

        return cls(post_data)

    def __str__(self):
        """
        :return: string representation by writing back to JSON string
        """
        return json_complex_str(self._json)

    def __repr__(self):
        return '<JSONContainer (token: %s)>' % self.get_token()

    def token_filter(self, token_path, token_value):
        """
        Only return tokens for strings and None (which is null in JSON)
        :see: https://github.com/andresriancho/w3af/issues/12000
        """
        if token_value is None:
            return True

        if isinstance(token_value, basestring):
            return True

        return False

    def iter_setters(self):
        """
        :yield: Tuples containing:
                    * The key name as a string
                    * The value as a string
                    * The setter to modify the value

                Only for the tokens which have a value with type "string" or
                null, this is required, since we don't want to fuzz something
                which was a number with a string like "abc", it will simply
                break the server-side framework parsing and don't return
                anything useful.
        """
        for key, val, setter in json_iter_setters(self._json):

            path = (key,)

            if self.token_filter(path, val):
                yield key, val, path, setter

    def get_short_printable_repr(self):
        """
        :return: A string with a short printable representation of self
        """
        if self.get_token() is not None:
            # I want to show the token variable and value in the output
            token = self.get_token()
            dt_str = '%s=%s' % (filter_non_printable(token.get_name()),
                                filter_non_printable(token.get_value()))
            return '...%s...' % dt_str[:self.MAX_PRINTABLE-6]
        else:
            # I'll simply show the first N parameter and values until the
            # MAX_PRINTABLE is achieved
            return filter_non_printable(str(self))[:self.MAX_PRINTABLE]

    def get_headers(self):
        return list(self._headers.items())

    def set_header(self, name, value):
        if not isinstance(name, basestring):
            raise TypeError('Header name must be a string.')

        if not isinstance(value, basestring):
            raise TypeError('Header value must be a string.')

        self._headers[name] = value
