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
import copy

from w3af.core.data.dc.token import DataToken
from w3af.core.data.dc.data_container import DataContainer
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
    def __init__(self, json_post_data, encoding=UTF8):
        """
        :param json_post_data: The XMLRPC call as string
        """
        DataContainer.__init__(self, encoding=encoding)

        if not isinstance(json_post_data, basestring):
            raise TypeError(ERR_MSG % json_post_data)

        if not JSONContainer.is_json(json_post_data):
            raise ValueError(ERR_MSG % json_post_data[:50])

        self._json = None
        self._raw_json = None

        self.parse_json(json_post_data)

    def __reduce__(self):
        return self.__class__, (self._raw_json,), {}

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
    def from_postdata(cls, post_data):
        return cls(post_data)

    def __str__(self):
        """
        :return: string representation by writing back to JSON string
        """
        return json_complex_str(self._json)

    def iter_bound_tokens(self):
        """
        :see: https://github.com/andresriancho/w3af/issues/580
        :see: Mostly used in Mutant._create_mutants_worker
        :yield: Tuples with:
                    - A copy of self
                    - A token set to the right location in the copy of self
        """
        for k, v, setter in self.iter_setters():
            token = DataToken(k, v)

            dcc = copy.deepcopy(self)
            dcc.set_token(k, token=token)
            dcc.token = token

            yield dcc, token

    def iter_setters(self):
        """
        :yield: Tuples containing:
                    * The key name as a string
                    * The value as a string
                    * The setter to modify the value
        """
        for k, v, setter in json_iter_setters(self._json):
            yield k, v, setter

    def set_token(self, key_name, token=None):
        """
        Sets the token in the DataContainer to point to the variable specified
        in key_name. The key_name is a string which represents "the path" to
        the location in the json.

        :raises: An exception when the DataContainer does NOT contain the
                 specified path in *args to find the variable
        :return: The token if we were able to set it in the DataContainer
        """
        for k, v, setter in self.iter_setters():
            if key_name == k:
                if token is None:
                    token = DataToken(k, v)

                setter(token)
                self.token = token

                return token

        raise RuntimeError('Invalid token path %s' % key_name)

    def get_short_printable_repr(self):
        """
        :return: A string with a short printable representation of self
        """
        if len(str(self)) <= self.MAX_PRINTABLE:
            return str(self)

        if self.get_token() is not None:
            # I want to show the token variable and value in the output
            for k, v, _ in self.iter_setters():
                if isinstance(v, DataToken):
                    dt_str = '%s=%s' % (v.get_name(), v.get_value())
                    return '...%s...' % dt_str[:self.MAX_PRINTABLE]
        else:
            # I'll simply show the first N parameter and values until the
            # MAX_PRINTABLE is achieved
            return str(self)[:self.MAX_PRINTABLE]
